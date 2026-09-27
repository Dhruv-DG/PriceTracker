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
    PlatformHistory, HistoricalPriceResult, ConfidenceLevel, SearchStatusResponse
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
        
        t_start = time.time()
        logger.info(f"search_started: query='{request.query}'")

        try:
            # Step 1: Parse the query
            parsed_query = await llm_service.parse_query(request.query)
            t_parse = time.time()
            logger.info(f"Parsed query: {parsed_query} (took {round((t_parse - t_start)*1000)}ms)")

            # Step 2: Check cache
            cache_key = make_cache_key(request.query)
            cached = await search_cache.get(cache_key)
            if cached:
                logger.info("Returning cached result")
                return cached

            # Step 3: Search for products
            search_query = parsed_query.search_query or request.query
            search_results = await self.search_provider.search(search_query)
            t_search = time.time()
            logger.info(f"candidate_count: {len(search_results)} (took {round((t_search - t_parse)*1000)}ms)")

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
            t_filter = time.time()
            logger.info(f"candidate_matched: {len(product_results)} (took {round((t_filter - t_search)*1000)}ms)")

            # Step 5: Build product info
            product = self._build_product_info(parsed_query, request.query)

            # Step 6: Build provisional prices (fast)
            current_prices = self._build_provisional_prices(product_results)
            t_prices = time.time()
            logger.info(f"Generated {len(current_prices)} provisional prices (took {round((t_prices - t_filter)*1000)}ms)")

            if not current_prices:
                warnings.append("Could not find any market candidates")

            # Create Search record in database
            search_id = None
            product_id = None
            if not settings.is_demo_mode:
                from app.models.models import Search
                async with async_session() as session:
                    search_record = Search(
                        query=request.query,
                        parsed_query=parsed_query.model_dump(),
                        status="ENRICHING",
                        product_id=product_id
                    )
                    session.add(search_record)
                    await session.commit()
                    search_id = search_record.id

            latency = round((time.time() - start_time) * 1000, 1)

            response = SearchResponse(
                search_id=search_id,
                query=request.query,
                parsed_query=parsed_query,
                product=product,
                current_prices=current_prices,
                status="ENRICHING" if search_id else "COMPLETED",
                is_demo=settings.is_demo_mode,
                latency_ms=latency,
                errors=errors,
                warnings=warnings,
            )

            # Spawn background task for history and analytics
            if search_id:
                asyncio.create_task(self.enrich_search(
                    search_id=search_id,
                    product=product,
                    provisional_prices=current_prices,
                    parsed_query=parsed_query,
                    original_query=request.query,
                    start_time=start_time
                ))
            else:
                # If demo mode, just run it immediately? Or fake it. For now, just return.
                pass

            logger.info(f"search_initial_completed: query='{request.query}', latency={latency}ms")
            return response

        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            return SearchResponse(
                query=request.query,
                is_demo=settings.is_demo_mode,
                latency_ms=round((time.time() - start_time) * 1000, 1),
                status="FAILED",
                errors=[str(e)],
            )

    async def enrich_search(
        self, 
        search_id: int, 
        product: ProductInfo, 
        provisional_prices: List[PriceData], 
        parsed_query: ParsedQuery,
        original_query: str,
        start_time: float
    ):
        """Background task to fetch verified prices, history and build dashboard."""
        try:
            logger.info(f"enrich_search started for search_id={search_id}")
            
            # Step 1: Verify provisional prices via adapters
            current_prices = await self._get_current_prices(
                provisional_prices, parsed_query, original_query
            )
            
            # Step 1.5: Persist to database if not in demo mode
            product_id = None
            if not settings.is_demo_mode and current_prices:
                try:
                    product_id = await self._save_observations_to_db(product, current_prices)
                except Exception as db_e:
                    logger.error(f"Failed to persist observations: {db_e}", exc_info=True)
            
            # Step 2: Get historical data (concurrent)
            platform_histories = await self._get_historical_data(product, current_prices)
            logger.info(f"Got history for {len(platform_histories)} platforms")

            # Step 2: Compute analytics and build dashboard
            dashboard = self._build_dashboard(product, current_prices, platform_histories)
            dashboard.is_demo = settings.is_demo_mode
            dashboard.latency_ms = round((time.time() - start_time) * 1000, 1)

            # Step 3: Cache the completed dashboard
            cache_key = f"dashboard_{search_id}"
            await search_cache.set(cache_key, dashboard, settings.CACHE_TTL_SEARCH)

            # Step 4: Update database status
            from app.models.models import Search
            from sqlalchemy import update
            async with async_session() as session:
                update_values = {
                    "status": "COMPLETED",
                    "latency_ms": dashboard.latency_ms,
                    "dashboard_data": dashboard.model_dump(mode='json')
                }
                if product_id:
                    update_values["product_id"] = product_id
                    
                stmt = update(Search).where(Search.id == search_id).values(**update_values)
                await session.execute(stmt)
                await session.commit()
                
            logger.info(f"enrich_search completed for search_id={search_id}")

        except Exception as e:
            logger.error(f"enrich_search error for search_id={search_id}: {e}", exc_info=True)
            from app.models.models import Search
            from sqlalchemy import update
            async with async_session() as session:
                stmt = update(Search).where(Search.id == search_id).values(status="FAILED")
                await session.execute(stmt)
                await session.commit()

    async def get_search_status(self, search_id: int) -> Optional[SearchStatusResponse]:
        from app.models.models import Search
        from sqlalchemy import select
        from app.schemas.schemas import SearchStatusResponse
        
        async with async_session() as session:
            stmt = select(Search).where(Search.id == search_id)
            result = await session.execute(stmt)
            search_record = result.scalar_one_or_none()
            
        if not search_record:
            return None
            
        cache_key = f"dashboard_{search_id}"
        dashboard_dict = await search_cache.get(cache_key)
        
        # If cache missed but we have it in DB, use the DB copy
        if not dashboard_dict and search_record.dashboard_data:
            dashboard_dict = search_record.dashboard_data
            # Re-cache it for future
            await search_cache.set(cache_key, dashboard_dict, settings.CACHE_TTL_SEARCH)
            
        is_completed = search_record.status == "COMPLETED"
        
        return SearchStatusResponse(
            status=search_record.status,
            current_prices_ready=True,
            history_ready=is_completed,
            analytics_ready=is_completed,
            completed=is_completed,
            dashboard=dashboard_dict
        )

    def _build_provisional_prices(self, results: List[SearchResultItem]) -> List[PriceData]:
        """Convert initial SearchResultItems into provisional PriceData objects."""
        prices = []
        for r in results:
            domain = r.domain.replace("www.", "")
            platform_name = r.metadata.get("platform_name") or r.metadata.get("source_store") or domain.split(".")[0].title()
            
            # Parse search engine price — may be a string like "₹82,900" or "$99,900"
            raw_price = r.metadata.get("extracted_price") or r.metadata.get("price")
            
            # If no price in metadata (organic results), try extracting from the snippet
            if not raw_price and r.snippet:
                import re
                # Match ₹ or Rs followed by numbers and commas
                snippet_match = re.search(r'(?:₹|Rs\.?\s*)\s*([\d,]+(?:\.\d+)?)', r.snippet, re.IGNORECASE)
                if snippet_match:
                    raw_price = snippet_match.group(1)

            search_price = self._parse_price_string(raw_price) if raw_price else None
            price_val = search_price if search_price else 0.0
            
            p = PriceData(
                platform=PlatformInfo(name=platform_name, domain=domain),
                url=r.url,
                price=price_val,
                effective_price=price_val,
                title=r.title or None,
                search_price=search_price,
                verification_status="PENDING",
                discovery_source=r.source,
                match_confidence=r.match_confidence,
                thumbnail=r.metadata.get("thumbnail"),
                rating=float(r.metadata["rating"]) if r.metadata.get("rating") else None,
                review_count=int(r.metadata["reviews"]) if r.metadata.get("reviews") else None,
            )
            prices.append(p)
            
        return prices

    @staticmethod
    def _parse_price_string(raw: any) -> Optional[float]:
        """Parse a price that may be a number or a string like '₹82,900'."""
        if isinstance(raw, (int, float)):
            return float(raw)
        if isinstance(raw, str):
            import re
            # Strip everything except digits and decimal point
            cleaned = re.sub(r'[^\d.]', '', raw)
            if cleaned:
                try:
                    return float(cleaned)
                except ValueError:
                    pass
        return None

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

        # 1. Deterministic filtering first
        needs_llm = []
        filtered = []
        seen_domains = set()
        
        # We need the product name to be at least partially present
        brand = (parsed_query.brand or "").lower()
        model = (parsed_query.model or "").lower()
        
        for r in unique_results:
            title = (r.title or "").lower()
            url = r.url.lower()
            normalized_domain = r.domain.replace("www.", "")
            
            if normalized_domain in seen_domains:
                continue
            
            # Fast reject: definitely not a product page (e.g. review, news, blog)
            if any(bad in url for bad in ["/review", "/news", "/blog", "forum", "/article"]):
                continue
                
            # Fast accept: highly likely a product page and matches brand/model
            if brand and model and brand in title and model in title:
                # If it's a known e-commerce URL structure
                if any(good in url for good in ["/p/", "/dp/", "/product/", "/itm/", "buy", "shop"]):
                    r.is_product_page = True
                    r.relevance_score = 0.9
                    
                    # Estimate confidence
                    if parsed_query.storage and parsed_query.storage.lower() in title and \
                       parsed_query.color and parsed_query.color.lower() in title:
                        r.match_confidence = "EXACT"
                    elif parsed_query.storage and parsed_query.storage.lower() in title:
                        r.match_confidence = "HIGH"
                    else:
                        r.match_confidence = "MEDIUM"
                        
                    filtered.append(r)
                    seen_domains.add(normalized_domain)
                    continue
                    
            # For shopping results from serper, they are almost definitely products
            if r.source == "serper_shopping":
                r.is_product_page = True
                r.relevance_score = 0.8
                r.match_confidence = "HIGH" if (brand in title and model in title) else "MEDIUM"
                filtered.append(r)
                seen_domains.add(normalized_domain)
                continue
            
            # Ambiguous: send to LLM or use rule-based fallback
            needs_llm.append(r)

        # 2. If LLM is available, classify ambiguous results in a single batch. Otherwise, use generous rule-based.
        if needs_llm and not llm_service._circuit_open:
            try:
                candidates_data = [
                    {"title": r.title, "url": r.url, "snippet": r.snippet} 
                    for r in needs_llm
                ]
                batch_classifications = await llm_service.batch_classify_search_results(candidates_data)
                
                if len(batch_classifications) == len(needs_llm):
                    for idx, classification in enumerate(batch_classifications):
                        result = needs_llm[idx]
                        domain_norm = result.domain.replace("www.", "")
                        
                        if domain_norm in seen_domains:
                            continue
                            
                        # Strictly enforce that it must be an ecommerce platform
                        if classification.get("is_ecommerce") and classification.get("type") == "product_page":
                            result.is_product_page = True
                            result.relevance_score = classification.get("confidence", 0.5)
                            result.match_confidence = "MEDIUM" if result.relevance_score > 0.5 else "LOW"
                            filtered.append(result)
                            seen_domains.add(domain_norm)
            except Exception as e:
                logger.warning(f"Batch classification failed: {e}")
        elif needs_llm:
            # LLM unavailable — use strict rule-based acceptance (only known ecommerce sites)
            KNOWN_ECOMMERCE = {
                "amazon", "flipkart", "myntra", "ajio", "tatacliq", "croma",
                "reliancedigital", "vijaysales", "poorvika", "apple", "samsung",
                "jiomart", "snapdeal", "meesho", "paytmmall", "nykaa", "shopatsc"
            }
            for r in needs_llm:
                domain_norm = r.domain.replace("www.", "")
                if domain_norm in seen_domains:
                    continue
                    
                domain_base = domain_norm.split(".")[0].lower()
                # Accept ONLY if it's a known e-commerce domain
                if domain_base in KNOWN_ECOMMERCE:
                    r.is_product_page = True
                    r.relevance_score = 0.6
                    r.match_confidence = "LOW"
                    filtered.append(r)
                    seen_domains.add(domain_norm)

        return filtered

    async def _get_current_prices(
        self,
        provisional_prices: List[PriceData],
        parsed_query: ParsedQuery,
        original_query: str,
    ) -> List[PriceData]:
        """Get current prices from all discovered platforms concurrently."""
        if settings.is_demo_mode:
            # In demo mode, provisional prices are already populated
            return provisional_prices

        # For real mode, extract prices concurrently
        from app.adapters.registry import adapter_registry
        
        logger.info(f"price_fetch_started: count={len(provisional_prices)}")

        # Concurrency control
        global_limit = getattr(settings, "PRICE_EXTRACTION_GLOBAL_CONCURRENCY", 10)
        domain_limit = getattr(settings, "PRICE_EXTRACTION_DOMAIN_CONCURRENCY", 2)
        timeout_sec = getattr(settings, "PRICE_EXTRACTION_TIMEOUT", 10)
        
        global_sem = asyncio.Semaphore(global_limit)
        domain_sems = {}

        async def extract_price(price_data: PriceData) -> PriceData:
            domain = price_data.platform.domain
            if domain not in domain_sems:
                domain_sems[domain] = asyncio.Semaphore(domain_limit)
                
            async with global_sem:
                async with domain_sems[domain]:
                    try:
                        adapter = adapter_registry.get_adapter(price_data.url)
                        if not adapter:
                            logger.warning(f"No adapter could handle {price_data.url}")
                            price_data.verification_status = "FAILED"
                            return price_data
                            
                        # Apply timeout to extraction
                        product = await asyncio.wait_for(
                            adapter.extract_product(price_data.url), 
                            timeout=timeout_sec
                        )
                        
                        if product and product.price:
                            price_data.verified_price = product.price
                            price_data.price = product.price
                            price_data.mrp = product.mrp
                            price_data.discount_pct = product.discount_pct
                            price_data.shipping = product.shipping
                            price_data.shipping_note = "Free" if product.shipping == 0 else ("Unknown" if product.shipping is None else f"₹{product.shipping}")
                            price_data.effective_price = product.effective_price
                            price_data.currency = product.currency
                            price_data.availability = product.availability
                            price_data.seller = product.seller
                            price_data.fulfilled_by = product.fulfilled_by
                            price_data.condition = product.condition
                            price_data.title = product.title
                            price_data.external_product_id = product.external_id
                            price_data.verification_status = "VERIFIED"
                        else:
                            price_data.verification_status = "FAILED"
                    except asyncio.TimeoutError:
                        logger.warning(f"Price extraction timed out for {price_data.url}")
                        price_data.verification_status = "FAILED"
                    except Exception as e:
                        logger.warning(f"Price extraction failed for {price_data.url}: {e}")
                        price_data.verification_status = "FAILED"
                        
                    return price_data

        tasks = [extract_price(p) for p in provisional_prices]
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
                
                # Use ASIN (external_product_id) for Keepa/Amazon, otherwise canonical name
                identifier = price.external_product_id if price.external_product_id and "amazon" in price.platform.domain.lower() else product.canonical_name
                
                history = await provider.get_history(
                    product_identifier=identifier,
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

    async def _save_observations_to_db(self, product_info: ProductInfo, current_prices: List[PriceData]) -> Optional[int]:
        """Persist product, platforms, listings, and price observations to the database.
        Returns the product ID. Raises exception on failure.
        """
        logger.info(f"database_write: start product={product_info.canonical_name} prices={len(current_prices)}")
        from sqlalchemy import select
        async with async_session() as session:
            try:
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
                return product.id
            except Exception as e:
                await session.rollback()
                logger.error(f"Error saving observations to DB: {e}", exc_info=True)
                raise


# Global orchestrator instance
search_orchestrator = SearchOrchestrator()
