"""
Search orchestration service.
Coordinates: query parsing → search → filtering → extraction → history → analytics → dashboard.
This is the main brain of the application.
"""
import asyncio
import time
import logging
from typing import List, Optional, Dict
from datetime import datetime
from urllib.parse import urlparse

from app.config import settings
from app.schemas.schemas import (
    SearchRequest, SearchResponse, DashboardResponse, ParsedQuery,
    SearchResultItem, ProductInfo, PlatformInfo, PriceData,
    PlatformHistory, HistoricalPriceResult, ConfidenceLevel,
)
from app.services.llm_service import llm_service
from app.services.analytics import analytics_service
from app.adapters.demo import DemoAdapter, DEMO_PLATFORMS
from app.search.serper import SerperSearchProvider
from app.search.demo import DemoSearchProvider
from app.history.demo import DemoHistoricalProvider
from app.history.registry import history_registry
from app.cache import search_cache, price_cache, make_cache_key
from app.database import async_session
from app.models.models import Product, Platform, ProductListing, PriceObservation, SourceType

logger = logging.getLogger(__name__)


class SearchOrchestrator:
    """
    Main search orchestration engine.
    Implements the staged pipeline:
    Query → Parse → Search → Filter → Extract → Match → History → Analytics → Dashboard
    """

    def __init__(self):
        # Initialize providers
        if settings.is_demo_mode:
            self.search_provider = DemoSearchProvider()
            self.history_provider = DemoHistoricalProvider()
            self.demo_adapter = DemoAdapter()
            self.history_registry = None
        else:
            self.search_provider = SerperSearchProvider()
            self.history_provider = None
            self.history_registry = history_registry
            self.demo_adapter = None

            # Try real search, fallback to demo
            if not settings.SERPER_API_KEY:
                self.search_provider = DemoSearchProvider()

    async def execute_search(self, request: SearchRequest) -> SearchResponse:
        """Execute the full search pipeline."""
        start_time = time.time()
        errors = []
        warnings = []
        
        logger.info(f"search_started: query='{request.query}'")

        try:
            # Step 1: Parse the query
            parsed_query = await llm_service.parse_query(request.query)
            logger.info(f"Parsed query: {parsed_query}")

            # Step 2: Check cache
            cache_key = make_cache_key(request.query)
            cached = await search_cache.get(cache_key)
            if cached:
                logger.info("Returning cached result")
                return cached

            # Step 3: Search for products
            search_query = parsed_query.search_query or request.query
            search_results = await self.search_provider.search(search_query)
            logger.info(f"candidate_count: {len(search_results)}")

            if not search_results:
                warnings.append("No search results found")
                return SearchResponse(
                    query=request.query,
                    parsed_query=parsed_query,
                    is_demo=settings.is_demo_mode,
                    latency_ms=round((time.time() - start_time) * 1000, 1),
                    warnings=warnings,
                )

            # Step 4: Filter and classify results
            product_results = await self._filter_results(search_results, parsed_query)
            logger.info(f"candidate_matched: {len(product_results)}")

            # Step 5: Build product info
            product = self._build_product_info(parsed_query, request.query)

            # Step 6: Get current prices (concurrent)
            current_prices = await self._get_current_prices(
                product_results, parsed_query, request.query
            )
            logger.info(f"Got {len(current_prices)} current prices")

            if not current_prices:
                warnings.append("Could not extract prices from any platform")

            # Step 7: Get historical data (concurrent)
            platform_histories = await self._get_historical_data(
                product, current_prices
            )
            logger.info(f"Got history for {len(platform_histories)} platforms")

            # Step 8: Compute analytics
            dashboard = self._build_dashboard(
                product, current_prices, platform_histories
            )
            dashboard.is_demo = settings.is_demo_mode

            latency = round((time.time() - start_time) * 1000, 1)
            dashboard.latency_ms = latency

            # Step 9: Persist to database if not in demo mode
            if not settings.is_demo_mode and current_prices:
                try:
                    await self._save_observations_to_db(product, current_prices)
                except Exception as db_e:
                    logger.error(f"Failed to persist observations: {db_e}", exc_info=True)
                    warnings.append("Data persistence failed. Results may not be saved for tracking.")

            response = SearchResponse(
                query=request.query,
                parsed_query=parsed_query,
                product=product,
                dashboard=dashboard,
                is_demo=settings.is_demo_mode,
                latency_ms=latency,
                errors=errors,
                warnings=warnings,
            )

            # Cache the result
            await search_cache.set(cache_key, response, settings.CACHE_TTL_SEARCH)

            logger.info(f"search_completed: query='{request.query}', latency={latency}ms")
            return response

        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            return SearchResponse(
                query=request.query,
                is_demo=settings.is_demo_mode,
                latency_ms=round((time.time() - start_time) * 1000, 1),
                errors=[str(e)],
            )

    async def _filter_results(
        self,
        results: List[SearchResultItem],
        parsed_query: ParsedQuery
    ) -> List[SearchResultItem]:
        """Filter search results to relevant product pages in parallel."""
        # Clean up URLs to avoid exact duplicates
        unique_results = []
        seen_urls = set()
        for r in results:
            url = r.url.split("?")[0] if "?" in r.url and "amazon" not in r.url else r.url
            if url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(r)

        # Parallelize classification
        async def classify_and_filter(result: SearchResultItem) -> Optional[SearchResultItem]:
            try:
                classification = await llm_service.classify_search_result(
                    result.title, result.url, result.snippet or ""
                )
                if classification.get("is_ecommerce") and classification.get("type") == "product_page":
                    result.is_product_page = True
                    result.relevance_score = classification.get("confidence", 0.5)
                    return result
            except Exception as e:
                logger.warning(f"Classification failed for {result.url}: {e}")
            return None

        tasks = [classify_and_filter(r) for r in unique_results]
        classified = await asyncio.gather(*tasks, return_exceptions=True)
        
        filtered = []
        for r in classified:
            if isinstance(r, SearchResultItem):
                filtered.append(r)

        return filtered

    async def _get_current_prices(
        self,
        product_results: List[SearchResultItem],
        parsed_query: ParsedQuery,
        original_query: str,
    ) -> List[PriceData]:
        """Get current prices from all discovered platforms concurrently."""
        if settings.is_demo_mode:
            return self._get_demo_prices(product_results, original_query)

        # For real mode, extract prices concurrently
        from app.adapters.registry import adapter_registry
        
        logger.info(f"price_fetch_started: count={len(product_results)}")

        async def extract_price(result: SearchResultItem) -> Optional[PriceData]:
            try:
                adapter = adapter_registry.get_adapter(result.url)
                if not adapter:
                    logger.warning(f"No adapter could handle {result.url}")
                    return None
                    
                product = await adapter.extract_product(result.url)
                if product and product.price:
                    domain = result.domain.replace("www.", "")
                    platform_name = result.metadata.get("platform_name") or domain.split(".")[0].title()

                    return PriceData(
                        platform=PlatformInfo(
                            name=platform_name,
                            domain=domain,
                        ),
                        url=result.url,
                        price=product.price,
                        mrp=product.mrp,
                        discount_pct=product.discount_pct,
                        shipping=product.shipping,
                        shipping_note="Free" if product.shipping == 0 else ("Unknown" if product.shipping is None else f"₹{product.shipping}"),
                        effective_price=product.effective_price,
                        currency=product.currency,
                        availability=product.availability,
                        seller=product.seller,
                        fulfilled_by=product.fulfilled_by,
                        condition=product.condition,
                        title=product.title,
                        external_product_id=product.external_id,
                    )
            except Exception as e:
                logger.warning(f"Price extraction failed for {result.url}: {e}")
            return None

        tasks = [extract_price(r) for r in product_results]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        prices = []
        for r in results:
            if isinstance(r, PriceData):
                prices.append(r)
            elif isinstance(r, Exception):
                logger.warning(f"Price extraction error: {r}")

        logger.info(f"price_fetch_completed: fetched={len(prices)}")
        return sorted(prices, key=lambda p: p.effective_price)

    def _get_demo_prices(
        self,
        product_results: List[SearchResultItem],
        query: str
    ) -> List[PriceData]:
        """Generate demo prices for all discovered platforms."""
        demo = DemoAdapter()
        prices = []

        for result in product_results:
            domain = result.domain.replace("www.", "")
            platform_info_data = DEMO_PLATFORMS.get(domain)

            if platform_info_data:
                product = demo.generate_for_query(query, domain, result.url)
                platform_name = platform_info_data["name"]

                prices.append(PriceData(
                    platform=PlatformInfo(
                        name=platform_name,
                        domain=domain,
                    ),
                    url=result.url,
                    price=product.price,
                    mrp=product.mrp,
                    discount_pct=product.discount_pct,
                    shipping=0,
                    shipping_note="Free",
                    effective_price=product.effective_price,
                    currency="INR",
                    availability=product.availability,
                    seller=product.seller,
                    fulfilled_by=product.fulfilled_by,
                    condition="new",
                    title=query,
                ))

        return sorted(prices, key=lambda p: p.effective_price)

    async def _get_historical_data(
        self,
        product: ProductInfo,
        current_prices: List[PriceData]
    ) -> List[PlatformHistory]:
        """Get historical data for all platforms concurrently."""
        async def get_history(price: PriceData) -> Optional[PlatformHistory]:
            try:
                if settings.is_demo_mode:
                    provider = self.history_provider
                else:
                    provider = await self.history_registry.get_provider(price.platform.domain)
                    
                logger.info(f"history_provider_used: platform={price.platform.domain} provider={provider.name}")
                history = await provider.get_history(
                    product_identifier=product.canonical_name,
                    platform_domain=price.platform.domain,
                )
                if history and history.observations:
                    obs_prices = [o.price for o in history.observations]
                    return PlatformHistory(
                        platform=price.platform,
                        history=history,
                        historical_low=min(obs_prices),
                        historical_high=max(obs_prices),
                        historical_avg=round(sum(obs_prices) / len(obs_prices), 2),
                    )
            except Exception as e:
                logger.warning(f"history_provider_failed: platform={price.platform.domain} error={str(e)}")
            return None

        tasks = [get_history(p) for p in current_prices]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        histories = []
        for r in results:
            if isinstance(r, PlatformHistory):
                histories.append(r)

        return histories

    def _build_product_info(self, parsed: ParsedQuery, original_query: str) -> ProductInfo:
        """Build canonical product info from parsed query."""
        # Build a robust canonical name instead of using raw search query
        components = []
        if parsed.brand:
            components.append(parsed.brand)
        if parsed.model:
            # Avoid repeating brand if model already starts with it
            model = parsed.model
            if parsed.brand and model.lower().startswith(parsed.brand.lower()):
                model = model[len(parsed.brand):].strip()
            if model:
                components.append(model)
        if parsed.variant:
            components.append(parsed.variant)
        if parsed.storage:
            components.append(parsed.storage)
        if parsed.ram:
            components.append(parsed.ram)
        if parsed.color:
            components.append(parsed.color)
            
        canonical_name = " ".join(components) if components else original_query
        
        return ProductInfo(
            canonical_name=canonical_name,
            brand=parsed.brand,
            model=parsed.model,
            variant=parsed.variant,
            category=parsed.category,
            storage=parsed.storage,
            ram=parsed.ram,
            color=parsed.color,
            condition=parsed.condition,
        )

    def _build_dashboard(
        self,
        product: ProductInfo,
        current_prices: List[PriceData],
        platform_histories: List[PlatformHistory],
    ) -> DashboardResponse:
        """Build the complete dashboard response."""
        # Highlight cards
        highlights = analytics_service.compute_highlights(current_prices, platform_histories)

        # Current statistics
        current_stats = analytics_service.compute_statistics(
            [p.effective_price for p in current_prices]
        )
        current_stats.platforms_count = len(current_prices)

        # Historical statistics
        all_hist_prices = []
        for ph in platform_histories:
            all_hist_prices.extend([o.price for o in ph.history.observations])
        historical_stats = analytics_service.compute_statistics(all_hist_prices)

        # Volatility
        volatility = analytics_service.compute_volatility(platform_histories)

        # Price movements
        current_avg = highlights.current_average
        movements = analytics_service.compute_price_movements(platform_histories, current_avg)

        # Average price over time
        avg_over_time = analytics_service.compute_average_price_over_time(platform_histories)

        # Price position
        position = None
        if current_avg:
            position = analytics_service.compute_price_position(current_avg, platform_histories)

        # Cheapest / most consistent
        cheapest_hist = analytics_service.find_cheapest_historical_platform(platform_histories)
        most_consistent, metric = analytics_service.find_most_consistent_platform(platform_histories)

        # Data sources
        data_sources = analytics_service.build_data_sources(platform_histories)

        # Current cheapest platform
        cheapest_current = current_prices[0].platform.name if current_prices else None

        return DashboardResponse(
            product=product,
            highlights=highlights,
            current_prices=current_prices,
            platform_histories=platform_histories,
            average_price_over_time=avg_over_time,
            price_movements=movements,
            current_statistics=current_stats,
            historical_statistics=historical_stats,
            volatility=volatility,
            price_position=position,
            data_sources=data_sources,
            cheapest_platform=cheapest_current,
            cheapest_historical_platform=cheapest_hist,
            most_consistent_platform=most_consistent,
            most_consistent_metric=metric,
        )

    async def _save_observations_to_db(self, product_info: ProductInfo, current_prices: List[PriceData]):
        """Persist product, platforms, listings, and price observations to the database."""
        try:
            logger.info(f"database_write: start product={product_info.canonical_name} prices={len(current_prices)}")
            from sqlalchemy import select
            async with async_session() as session:
                # 1. Get or create Product
                stmt = select(Product).where(Product.canonical_name == product_info.canonical_name)
                result = await session.execute(stmt)
                product = result.scalar_one_or_none()
                
                if not product:
                    product = Product(
                        canonical_name=product_info.canonical_name,
                        brand=product_info.brand,
                        model=product_info.model,
                        variant=product_info.variant,
                        category=product_info.category,
                    )
                    session.add(product)
                    await session.flush()

                # 2. Process each price data point
                for price_data in current_prices:
                    # Get or create Platform
                    stmt = select(Platform).where(Platform.domain == price_data.platform.domain)
                    result = await session.execute(stmt)
                    platform = result.scalar_one_or_none()
                    
                    if not platform:
                        platform = Platform(
                            name=price_data.platform.name,
                            domain=price_data.platform.domain,
                        )
                        session.add(platform)
                        await session.flush()
                        
                    # Get or create ProductListing
                    # Preserve seller distinctions and variant distinctions
                    conditions = [
                        ProductListing.product_id == product.id,
                        ProductListing.platform_id == platform.id
                    ]
                    
                    if price_data.external_product_id:
                        conditions.append(ProductListing.external_product_id == price_data.external_product_id)
                    else:
                        conditions.append(ProductListing.url == price_data.url)
                        
                    if price_data.seller:
                        conditions.append(ProductListing.seller == price_data.seller)
                        
                    stmt = select(ProductListing).where(*conditions)
                    result = await session.execute(stmt)
                    listing = result.scalar_one_or_none()
                    
                    if not listing:
                        listing = ProductListing(
                            product_id=product.id,
                            platform_id=platform.id,
                            url=price_data.url,
                            title=price_data.title,
                            seller=price_data.seller,
                            external_product_id=price_data.external_product_id,
                        )
                        session.add(listing)
                        await session.flush()
                        
                    # Add PriceObservation
                    observation = PriceObservation(
                        listing_id=listing.id,
                        price=price_data.price,
                        mrp=price_data.mrp,
                        shipping=price_data.shipping,
                        effective_price=price_data.effective_price,
                        currency=price_data.currency,
                        source="live_search",
                        source_type=SourceType.OWN_TRACKER.value,
                        provider="serper_extraction",
                        confidence=1.0,
                    )
                    session.add(observation)
                
                await session.commit()
                logger.info(f"Saved {len(current_prices)} observations for {product_info.canonical_name} to DB")
        except Exception as e:
            logger.error(f"Error saving observations to DB: {e}", exc_info=True)


# Global orchestrator instance
search_orchestrator = SearchOrchestrator()
