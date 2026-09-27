"""
LLM Service — handles query understanding and product matching.
Uses Google Gemini API (free tier) with a demo fallback.
"""
import json
import re
import httpx
import logging
from typing import Optional, Dict, Any

from app.config import settings
from app.schemas.schemas import ParsedQuery

logger = logging.getLogger(__name__)


class LLMService:
    """LLM service for query understanding and product matching."""

    GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL

    async def parse_query(self, query: str) -> ParsedQuery:
        """
        Parse a natural-language product query into structured attributes.
        Uses LLM when available, falls back to rule-based parsing.
        """
        if self.api_key and not settings.is_demo_mode:
            try:
                return await self._llm_parse_query(query)
            except Exception as e:
                logger.warning(f"LLM parse failed, using fallback: {e}")

        return self._rule_based_parse(query)

    async def match_products(
        self,
        query_product: ParsedQuery,
        candidate_title: str
    ) -> Dict[str, Any]:
        """
        Determine if a candidate listing matches the queried product.
        Returns match confidence and reasoning.
        """
        if self.api_key and not settings.is_demo_mode:
            try:
                return await self._llm_match_product(query_product, candidate_title)
            except Exception as e:
                logger.warning(f"LLM match failed, using fallback: {e}")

        return self._rule_based_match(query_product, candidate_title)

    async def classify_search_result(self, title: str, url: str, snippet: str) -> Dict[str, Any]:
        """Classify a search result as product page, category page, etc."""
        if self.api_key and not settings.is_demo_mode:
            try:
                return await self._llm_classify(title, url, snippet)
            except Exception as e:
                logger.warning(f"LLM classify failed, using fallback: {e}")

        return self._rule_based_classify(title, url, snippet)

    # ─── Gemini LLM Implementations ─────────────────────────

    async def _llm_parse_query(self, query: str) -> ParsedQuery:
        """Use Gemini to parse a product query."""
        prompt = f"""Parse this product search query into structured attributes.
Return ONLY valid JSON with these fields:
{{
  "brand": "brand name or null",
  "model": "model name or null",
  "variant": "variant (e.g., Pro, Ultra, Standard) or null",
  "storage": "storage capacity or null",
  "ram": "RAM or null",
  "color": "color or null",
  "size": "size or null",
  "condition": "new or used or refurbished",
  "category": "product category",
  "search_query": "optimized search query for e-commerce sites"
}}

Query: "{query}"

Return ONLY the JSON object, no other text."""

        result = await self._call_gemini(prompt)
        if result:
            try:
                data = self._extract_json(result)
                return ParsedQuery(**data)
            except Exception as e:
                logger.warning(f"Failed to parse LLM response: {e}")

        return self._rule_based_parse(query)

    async def _llm_match_product(self, query_product: ParsedQuery, candidate_title: str) -> Dict[str, Any]:
        """Use Gemini to match a candidate product."""
        prompt = f"""Determine if this product listing matches the searched product.

Searched product:
- Brand: {query_product.brand}
- Model: {query_product.model}
- Variant: {query_product.variant}
- Storage: {query_product.storage}
- Color: {query_product.color}
- RAM: {query_product.ram}

Candidate listing title: "{candidate_title}"

Return ONLY valid JSON:
{{
  "is_match": true/false,
  "confidence": 0.0 to 1.0,
  "reason": "brief explanation",
  "variant_match": true/false,
  "extracted_brand": "brand from title",
  "extracted_model": "model from title"
}}

IMPORTANT: Different storage sizes (128GB vs 256GB), different variants (Pro vs Standard), 
or different colors are NOT the same product. Be strict about variant matching."""

        result = await self._call_gemini(prompt)
        if result:
            try:
                return self._extract_json(result)
            except Exception:
                pass

        return self._rule_based_match(query_product, candidate_title)

    async def _llm_classify(self, title: str, url: str, snippet: str) -> Dict[str, Any]:
        """Use Gemini to classify a search result."""
        prompt = f"""Classify this search result. Is it a product page on an e-commerce site?

Title: "{title}"
URL: {url}
Snippet: "{snippet}"

Return ONLY valid JSON:
{{
  "type": "product_page" | "category_page" | "search_page" | "blog" | "review" | "other",
  "is_ecommerce": true/false,
  "confidence": 0.0 to 1.0,
  "platform_name": "store name or null"
}}"""

        result = await self._call_gemini(prompt)
        if result:
            try:
                return self._extract_json(result)
            except Exception:
                pass

        return self._rule_based_classify(title, url, snippet)

    async def _call_gemini(self, prompt: str) -> Optional[str]:
        """Call the Gemini API."""
        if not self.api_key:
            return None

        url = self.GEMINI_URL.format(model=self.model)
        params = {"key": self.api_key}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 1024,
            }
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(url, json=payload, params=params)
                response.raise_for_status()
                data = response.json()

            candidates = data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    return parts[0].get("text", "")

        except Exception as e:
            logger.error(f"Gemini API error: {e}")

        return None

    # ─── Rule-Based Fallbacks ────────────────────────────────

    def _rule_based_parse(self, query: str) -> ParsedQuery:
        """Parse query using deterministic rules."""
        q = query.strip()
        words = q.split()

        # Known brands
        brands = {
            "apple": "Apple", "samsung": "Samsung", "sony": "Sony",
            "google": "Google", "oneplus": "OnePlus", "xiaomi": "Xiaomi",
            "realme": "Realme", "oppo": "OPPO", "vivo": "Vivo",
            "dell": "Dell", "hp": "HP", "lenovo": "Lenovo", "asus": "ASUS",
            "nike": "Nike", "adidas": "Adidas", "jbl": "JBL", "bose": "Bose",
            "lg": "LG", "mi": "Xiaomi", "boat": "boAt", "nothing": "Nothing",
        }

        brand = None
        for word in words:
            if word.lower() in brands:
                brand = brands[word.lower()]
                break

        # iPhone implies Apple
        if not brand and any("iphone" in w.lower() for w in words):
            brand = "Apple"
        if not brand and any("macbook" in w.lower() for w in words):
            brand = "Apple"
        if not brand and any("ipad" in w.lower() for w in words):
            brand = "Apple"
        if not brand and any("airpod" in w.lower() for w in words):
            brand = "Apple"
        if not brand and any("galaxy" in w.lower() for w in words):
            brand = "Samsung"
        if not brand and any("pixel" in w.lower() for w in words):
            brand = "Google"

        # Storage detection
        storage = None
        storage_match = re.search(r'(\d+)\s*(gb|tb)', q, re.IGNORECASE)
        if storage_match:
            amount = storage_match.group(1)
            unit = storage_match.group(2).upper()
            storage = f"{amount}{unit}"

        # RAM detection
        ram = None
        ram_match = re.search(r'(\d+)\s*gb\s*ram', q, re.IGNORECASE)
        if ram_match:
            ram = f"{ram_match.group(1)}GB"

        # Color detection
        colors = ["black", "white", "blue", "red", "green", "gold", "silver",
                  "pink", "purple", "titanium", "natural", "midnight", "starlight"]
        color = None
        for c in colors:
            if c in q.lower():
                color = c.title()
                break

        # Category
        category = "electronics"
        if any(w in q.lower() for w in ["shoe", "sneaker", "air max"]):
            category = "footwear"
        elif any(w in q.lower() for w in ["shirt", "tshirt", "jacket"]):
            category = "clothing"

        return ParsedQuery(
            brand=brand,
            model=q,  # Use full query as model for now
            storage=storage,
            ram=ram,
            color=color,
            category=category,
            condition="new",
            search_query=q,
        )

    def _rule_based_match(self, query_product: ParsedQuery, candidate_title: str) -> Dict[str, Any]:
        """Match using simple string comparison."""
        title_lower = candidate_title.lower()
        query_str = (query_product.search_query or query_product.model or "").lower()

        # Check key attributes
        words = query_str.split()
        matching_words = sum(1 for w in words if w in title_lower)
        match_ratio = matching_words / max(len(words), 1)

        # Check storage match
        storage_match = True
        if query_product.storage:
            if query_product.storage.lower() not in title_lower:
                storage_match = False

        # Check brand match
        brand_match = True
        if query_product.brand:
            if query_product.brand.lower() not in title_lower:
                brand_match = False

        is_match = match_ratio > 0.5 and storage_match and brand_match
        confidence = min(match_ratio + (0.2 if storage_match else 0) + (0.2 if brand_match else 0), 1.0)

        return {
            "is_match": is_match,
            "confidence": round(confidence, 2),
            "reason": f"Word match: {match_ratio:.0%}, Storage: {storage_match}, Brand: {brand_match}",
            "variant_match": storage_match,
        }

    def _rule_based_classify(self, title: str, url: str, snippet: str) -> Dict[str, Any]:
        """Classify using URL patterns."""
        ecommerce_domains = [
            "amazon.in", "flipkart.com", "croma.com", "reliancedigital.in",
            "vijaysales.com", "myntra.com", "ajio.com", "tatacliq.com",
            "snapdeal.com", "paytmmall.com", "apple.com",
        ]

        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "").lower()

        is_ecommerce = any(d in domain for d in ecommerce_domains)

        # Detect page type from URL patterns
        path = parsed.path.lower()
        if any(p in path for p in ["/dp/", "/product/", "/itm/", "/p/"]):
            page_type = "product_page"
        elif any(p in path for p in ["/category/", "/search", "/s?", "/explore/"]):
            page_type = "category_page"
        elif any(p in path for p in ["/blog/", "/review/", "/article/"]):
            page_type = "blog"
        else:
            page_type = "product_page" if is_ecommerce else "other"

        # Get platform name
        platform_names = {
            "amazon.in": "Amazon", "flipkart.com": "Flipkart",
            "croma.com": "Croma", "reliancedigital.in": "Reliance Digital",
            "vijaysales.com": "Vijay Sales", "myntra.com": "Myntra",
        }
        platform_name = None
        for d, name in platform_names.items():
            if d in domain:
                platform_name = name
                break

        return {
            "type": page_type,
            "is_ecommerce": is_ecommerce,
            "confidence": 0.8 if is_ecommerce else 0.5,
            "platform_name": platform_name,
        }

    def _extract_json(self, text: str) -> dict:
        """Extract JSON from LLM response text."""
        # Try direct parse
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # Try extracting from code block
        match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1).strip())

        # Try finding JSON object
        match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))

        raise ValueError(f"No JSON found in response: {text[:200]}")


# Global LLM service instance
llm_service = LLMService()
