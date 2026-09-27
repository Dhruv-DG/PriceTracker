# MASTER PROMPT

## Build a Unified E-commerce Price Intelligence & Historical Price Dashboard

You are an expert full-stack engineer, software architect, data engineer, and web-data extraction engineer.

Build a complete, runnable MVP of a web application that allows a user to enter a natural-language product query and receive a comprehensive price-intelligence dashboard showing:

* Current prices across multiple e-commerce platforms
* Historical prices for each platform wherever historical data is available
* Average price over time
* Lowest and highest prices
* Current price vs historical average
* Current price vs historical low/high
* Price trends
* Price volatility
* Price differences between platforms
* Product/variant information
* Historical data source and confidence/provenance
* Additional useful price insights
* Automatic ongoing tracking for products discovered by users

The application should prioritize **speed, modularity, reliability, extensibility, and transparency about where data came from**.

Do NOT build a simplistic fixed-store price comparison website.

The central idea is:

> The user searches for a product, the system dynamically discovers relevant e-commerce product listings, resolves which results represent the same product/variant, retrieves current prices and historical prices from whatever legitimate data sources are available, normalizes everything into a common model, and presents a rich historical price-intelligence dashboard.

---

# 1. CORE USER EXPERIENCE

The user should be able to enter queries such as:

* "iPhone 17 256GB Black"
* "Sony WH-1000XM6"
* "Samsung Galaxy S26 Ultra 512GB"
* "best price for Nike Air Max 270 size 9"
* "MacBook Air M4 16GB 512GB"

The user should NOT need to know which e-commerce websites carry the product.

The system should dynamically discover relevant product listings.

Example:

User enters:

"iPhone 17 256GB Black"

The system might discover:

* Amazon
* Flipkart
* Croma
* Reliance Digital
* Vijay Sales
* Apple
* Other relevant e-commerce sites

The system should then:

1. Understand the requested product.
2. Search for candidate product listings.
3. Filter irrelevant search results.
4. Identify e-commerce product pages.
5. Resolve whether each listing corresponds to the requested product and variant.
6. Retrieve current price information.
7. Retrieve historical price information wherever a legitimate historical data source/API exists.
8. Fall back to the application's own historical database when external historical data is unavailable.
9. Normalize all information.
10. Store the result.
11. Render a comprehensive dashboard.
12. Optionally begin tracking the discovered products for future updates.

---

# 2. IMPORTANT ARCHITECTURAL PRINCIPLE

DO NOT hardcode the application around a fixed list of stores.

Do NOT make the core system:

Amazon → Flipkart → Croma → etc.

Instead build an extensible adapter/provider architecture.

There are two different concepts:

## A. E-commerce adapters

Responsible for extracting CURRENT information from a specific website.

Example:

```text
adapters/
    base.py
    amazon.py
    flipkart.py
    croma.py
    reliance_digital.py
    myntra.py
```

Each adapter implements a common interface.

## B. Historical-price providers

Responsible for retrieving historical information.

Example:

```text
history/
    base.py
    keepa.py
    priceapi.py
    own_database.py
```

Historical data should NOT be assumed to exist for every website.

The system should dynamically determine which historical provider can serve a particular product.

---

# 3. HISTORICAL DATA STRATEGY

This is a critical requirement.

The application must NOT assume that it has to wait days before historical data becomes available.

Use existing legitimate historical-price APIs/data providers wherever possible.

For example:

* Keepa for Amazon historical price data where applicable
* Other legitimate price-history APIs/providers where available
* The application's own historical database as a fallback

The architecture must support multiple historical data providers.

Conceptually:

```text
Product
   |
   +---- Current Price
   |       |
   |       +---- E-commerce Adapter
   |
   +---- Historical Price
           |
           +---- External Provider A
           |
           +---- External Provider B
           |
           +---- Own Historical Database
```

Do NOT scrape another price-tracker website merely because it displays historical data.

Prefer:

1. Official APIs
2. Licensed/legitimate third-party APIs
3. Publicly available structured data where permitted
4. Your own historical collection

Respect robots.txt, website terms, API terms, rate limits, authentication requirements, and applicable laws.

Never bypass CAPTCHA, anti-bot mechanisms, authentication, paywalls, or access controls.

---

# 4. EXTERNAL API ABSTRACTION

Do not hardcode Keepa or any other provider into the main application.

Create a generic interface:

```python
class HistoricalPriceProvider:
    async def get_history(self, product_identifier):
        ...
```

Providers should expose normalized results.

For example:

```python
HistoricalPriceResult(
    provider="keepa",
    product_id="...",
    currency="INR",
    observations=[...],
    start_date=...,
    end_date=...,
    confidence=...,
    source_url=...,
)
```

If an external provider does not support a particular product/site:

```text
provider unavailable
        ↓
try next provider
        ↓
own database
```

The application should gracefully handle:

* API unavailable
* API timeout
* API quota exceeded
* Product not found
* Historical data unavailable
* Partial historical data
* Authentication failure
* Invalid product identifier

---

# 5. SEARCH / DISCOVERY ENGINE

The system should have a search-provider abstraction.

Do not tightly couple the application to Google.

Create something like:

```text
search/
    base.py
    provider.py
```

Possible providers can include:

* Search API
* Google Shopping-compatible API
* SerpAPI or equivalent
* Other legitimate search providers

The application should receive normalized search results:

```python
SearchResult(
    title,
    url,
    domain,
    snippet,
    source,
    metadata
)
```

The rest of the application should not care which search provider produced the result.

---

# 6. SEARCH RESULT PIPELINE

Do not immediately send every result to an LLM.

Use a staged pipeline.

```text
User Query
    ↓
Search Provider
    ↓
10–20 candidate results
    ↓
URL normalization
    ↓
Domain extraction
    ↓
Deduplication
    ↓
E-commerce filtering
    ↓
Product-page detection
    ↓
Product extraction
    ↓
Product matching
    ↓
Final candidates
```

Only use the LLM where reasoning is actually required.

---

# 7. LLM RESPONSIBILITIES

The LLM should NOT be responsible for:

* Routing every website
* Scraping HTML
* Extracting every price
* Making network requests
* Replacing deterministic parsing

Use deterministic code wherever possible.

The LLM should primarily help with:

## Query understanding

Convert:

"black iPhone 17 256 gigs"

into:

```json
{
  "brand": "Apple",
  "model": "iPhone 17",
  "storage": "256GB",
  "color": "Black",
  "variant": "standard"
}
```

## Product matching

Determine whether:

"Apple iPhone 17 (Black, 256 GB)"

and

"Apple iPhone 17 256GB Black"

represent the same product.

It must distinguish:

* iPhone 17 vs iPhone 17 Pro
* 128GB vs 256GB
* Wi-Fi vs Cellular
* Different generations
* Different sizes
* Different colors when relevant
* Different configurations

## Search-result classification

Determine whether a candidate is:

* Relevant product
* Wrong product
* Category page
* Search page
* Blog
* Review
* Advertisement
* Marketplace listing
* Product page

Return structured JSON from the LLM.

Do NOT allow arbitrary natural-language output to drive application logic.

---

# 8. PRODUCT IDENTITY / NORMALIZATION

Create a canonical product model.

Example:

```json
{
  "brand": "Apple",
  "model": "iPhone 17",
  "variant": "Standard",
  "storage": "256GB",
  "ram": null,
  "color": "Black",
  "size": null,
  "condition": "new"
}
```

Where possible, identify products using:

* ASIN
* GTIN
* EAN
* UPC
* MPN
* SKU
* Manufacturer model number

Identifiers should be preferred over fuzzy title matching.

Build a product normalization layer.

---

# 9. E-COMMERCE ADAPTER SYSTEM

Create a common interface:

```python
class EcommerceAdapter:

    async def can_handle(self, url):
        ...

    async def extract_product(self, url):
        ...

    async def get_current_price(self, url):
        ...

    async def get_availability(self, url):
        ...

    async def get_product_details(self, url):
        ...
```

The main application must not contain website-specific scraping logic.

Example:

```text
adapter_registry.py

amazon.in → AmazonAdapter
flipkart.com → FlipkartAdapter
croma.com → CromaAdapter
...
```

The registry should resolve adapters using normalized domains.

Do NOT use an LLM to determine:

"amazon.in means amazon.py"

That should be deterministic and nearly instantaneous.

---

# 10. EXTRACTION STRATEGY

For each website, use the most reliable extraction strategy available.

Preferred order:

1. Embedded structured data / JSON-LD
2. Official APIs where available
3. Stable HTML selectors
4. Site-specific extraction logic
5. Browser automation only when necessary
6. LLM extraction only as a fallback

Do not make browser automation the default for every website.

Use lightweight HTTP requests where possible.

Use Playwright only for pages that genuinely require JavaScript rendering.

---

# 11. SPEED REQUIREMENT

The application should feel fast.

The search process should NOT be:

```text
Amazon
wait
Flipkart
wait
Croma
wait
Reliance
wait
...
```

Everything possible should run concurrently.

Use asynchronous I/O.

For example:

```python
results = await asyncio.gather(
    amazon_adapter.get_current_price(...),
    flipkart_adapter.get_current_price(...),
    croma_adapter.get_current_price(...),
    reliance_adapter.get_current_price(...)
)
```

Search result processing should also be concurrent where safe.

Implement:

* Async HTTP
* Connection pooling
* Timeouts
* Concurrent requests
* Result caching
* Provider-level caching
* Request deduplication

Do NOT allow one slow website to block the entire dashboard.

If one provider takes too long:

```text
Amazon ✓
Flipkart ✓
Croma ✓
Reliance timeout ⚠
```

The dashboard should still load.

---

# 12. TARGET PERFORMANCE

For a normal search:

Target:

```text
Query processing                 < 500ms
Search/discovery                 1–3 sec
Current price collection         1–5 sec
Dashboard initial render         < 5 sec where practical
```

Do not block the user interface waiting for slow historical providers.

Use progressive loading.

Example:

```text
0–1 sec
Product identified

1–3 sec
Current prices appear

2–5 sec
Historical data appears

Later
Additional analytics appear
```

---

# 13. DASHBOARD REQUIREMENTS

The dashboard is the most important visible component.

It should provide significantly more information than:

"Amazon ₹X, Flipkart ₹Y."

Design it as a price intelligence dashboard.

---

# 14. TOP-LEVEL HIGHLIGHT CARDS

Show prominent cards for:

### Current lowest price

```text
₹XX,XXX
Amazon
```

### Current highest price

```text
₹XX,XXX
Croma
```

### Current average price

Average across comparable available platforms.

### Historical lowest price

Lowest observed price in the available historical dataset.

### Historical highest price

Highest observed price.

### Historical average price

Average across the selected historical period.

### Current vs historical average

Example:

```text
Current: ₹29,999
Historical average: ₹32,499
Difference: -7.7%
```

### Current vs historical low

Example:

```text
Current: ₹29,999
Historical low: ₹27,499
Difference: +9.1%
```

### Price range

```text
₹27,499 — ₹35,999
```

---

# 15. MAIN PRICE COMPARISON TABLE

Show:

| Platform | Current Price | Shipping | Effective Price | Historical Low | Historical Avg | Historical High | Data Age |
| -------- | ------------- | -------- | --------------- | -------------- | -------------- | --------------- | -------- |

Include:

* Store/platform
* Current price
* MRP/list price when available
* Discount
* Shipping
* Effective price
* Availability
* Seller
* Product condition
* Historical low
* Historical average
* Historical high
* Last updated timestamp
* Historical data source

Make each platform expandable for more information.

---

# 16. PRICE HISTORY CHART

The main chart should allow:

* 7 days
* 30 days
* 90 days
* 6 months
* 1 year
* All available history

Plot separate lines for each e-commerce platform.

Example:

```text
Price
 ^
 |
 | Amazon ─────────╮
 |                  ╰────╮
 | Flipkart ───╮         ╰──
 |              ╰────
 |
 +--------------------------------> Time
```

Users should be able to toggle platforms on/off.

Tooltips should show:

* Date
* Platform
* Price
* Source

---

# 17. AVERAGE PRICE OVER TIME

This is specifically required.

Calculate an average price at each time point from the available platform observations.

For example:

```text
Date       Amazon    Flipkart    Croma    Average
--------------------------------------------------
Sep 1      80,000    79,500      81,000   80,167
Sep 2      79,500    78,999      81,000   79,833
Sep 3      79,999    78,499      80,500   79,666
```

Important:

DO NOT average platforms that don't have observations for that date without clearly explaining the missing-data treatment.

Show:

* Average price
* Number of platforms contributing
* Min price
* Max price

---

# 18. PRICE DISTRIBUTION / RANGE

Show:

```text
Current price distribution
Historical price distribution
```

Useful statistics:

* Mean
* Median
* Minimum
* Maximum
* Standard deviation
* Percentiles where enough data exists

Use appropriate visualizations.

---

# 19. PRICE VOLATILITY

Calculate useful measures such as:

* Standard deviation
* Average absolute daily change
* Percentage volatility
* Number of price changes
* Largest single price drop
* Largest single price increase

Example:

```text
Price volatility: Medium

Largest drop:
₹3,000 (-8.5%)

Largest increase:
₹2,500 (+7.1%)
```

Avoid pretending that a statistical metric is a financial prediction.

---

# 20. PRICE DROP ANALYSIS

Show:

### Recent price movement

```text
24h
7d
30d
90d
```

Example:

```text
24h    ↓ 2.3%
7d     ↓ 5.8%
30d    ↓ 8.1%
90d    ↑ 3.2%
```

---

# 21. "WHERE IS IT CHEAPEST?"

Provide:

```text
Current cheapest:
Amazon — ₹29,999
```

Also:

```text
Cheapest historical platform:
Flipkart

Most consistent platform:
Amazon
```

Be careful with terms like "most consistent": define the metric clearly, e.g. lowest price variance, rather than making an unexplained judgment.

---

# 22. HISTORICAL LOW CONTEXT

Show:

```text
Historical low: ₹27,499

Current price: ₹29,999

Current price is:
9.1% above historical low
```

This helps the user understand whether the current price is near the historical bottom.

---

# 23. PRICE POSITION INDICATOR

Create a simple indicator:

```text
Historical Low        Current             Historical High
     ₹27,499             ₹29,999              ₹35,999
        |------------------●--------------------|
```

Also calculate the normalized position within the historical range.

Clearly label this as a descriptive statistic, not a prediction.

---

# 24. DATA QUALITY / PROVENANCE

This is extremely important.

Every historical dataset should show:

```text
Historical data source:
Keepa

Coverage:
12 months

Last updated:
2 minutes ago

Observations:
1,842

Confidence:
High
```

For your own database:

```text
Source:
Your tracker

Tracking started:
27 Sep 2026

Coverage:
3 days

Observations:
18
```

Never make sparse data look like a complete historical record.

---

# 25. EXTERNAL VS OWN HISTORY

Clearly distinguish:

```text
External historical data
```

from:

```text
Data collected by this application
```

If multiple providers are merged, retain provenance for each observation.

Every price observation should ideally have:

```text
price
currency
timestamp
platform
source
source_type
provider
confidence
```

---

# 26. DATABASE DESIGN

Use PostgreSQL.

Create appropriate models along these lines:

```text
products
---------
id
canonical_name
brand
model
variant
category
identifiers
created_at
updated_at

platforms
---------
id
name
domain
country
currency

product_listings
----------------
id
product_id
platform_id
url
external_product_id
seller
availability
metadata

price_observations
------------------
id
listing_id
price
mrp
shipping
effective_price
currency
timestamp
source
source_type
provider
confidence

historical_sources
------------------
id
provider
platform
coverage_start
coverage_end
last_updated
metadata

searches
--------
id
query
timestamp

search_results
--------------
id
search_id
url
title
domain
relevance_score
matched_product_id

tracking_jobs
-------------
id
listing_id
frequency
last_run
next_run
status
```

Use appropriate indexes.

Especially index:

```text
listing_id + timestamp
product_id
platform_id
external_product_id
```

---

# 27. CACHE STRATEGY

Implement caching.

Cache:

* Search results
* Product resolution
* Current prices
* Historical API results
* Product metadata

Use Redis only if it materially improves the MVP.

Do not introduce unnecessary infrastructure if an in-process cache is sufficient for development.

Architecture should allow Redis later.

---

# 28. BACKGROUND TRACKING

When a user searches for a product and relevant listings are found, allow those listings to be tracked.

A scheduler periodically checks:

```text
Product A
 ├── Amazon
 ├── Flipkart
 └── Croma
```

and stores new observations.

This gradually builds your own historical database.

The scheduler must:

* Respect rate limits
* Avoid duplicate requests
* Handle failures
* Retry with backoff
* Record timestamps
* Track provider health

---

# 29. ALERTS

Design the system so price alerts can be added.

Examples:

```text
Notify me when iPhone 17 < ₹70,000
```

or:

```text
Notify me when price drops > 10%
```

For MVP, the alert infrastructure can be basic, but the database/schema should not prevent adding it later.

---

# 30. PRODUCT VARIANT SAFETY

This is extremely important.

NEVER compare:

```text
iPhone 17 128GB
```

with:

```text
iPhone 17 256GB
```

as if they were the same price.

Likewise:

```text
MacBook Air 16GB/256GB
```

must not be merged with:

```text
MacBook Air 8GB/256GB
```

Handle:

* Storage
* RAM
* Size
* Color
* Generation
* Model
* Region
* Connectivity
* Condition
* Bundle
* Pack size

where relevant.

---

# 31. MARKETPLACE / SELLER INFORMATION

If the platform is a marketplace, distinguish:

```text
Platform:
Amazon

Seller:
ABC Electronics

Fulfilled by:
Amazon

Condition:
New
```

where available.

Do not treat marketplace seller prices as identical to the platform's own inventory.

---

# 32. SHIPPING / EFFECTIVE PRICE

Where available, distinguish:

```text
Product price
+
Shipping
+
Known mandatory charges
=
Effective price
```

Do not falsely claim the effective price is complete if taxes/shipping are unavailable.

Clearly indicate:

```text
Shipping unknown
```

rather than assuming zero.

---

# 33. CURRENCY

Design the system for multiple currencies.

Store:

```text
amount
currency
```

Do not overwrite raw prices with converted values.

For India, default display can be INR.

But architecture should support USD, GBP, EUR, etc.

---

# 34. ERROR HANDLING

One broken source must never crash the whole dashboard.

Example:

```text
Amazon       ✓
Flipkart     ✓
Croma        ✓
Reliance     ⚠ unavailable
Keepa        ✓
Provider X   ⚠ timeout
```

The user should still receive the dashboard.

Return partial results gracefully.

---

# 35. API DESIGN

Create clean backend endpoints such as:

```text
POST /api/search

GET /api/products/{id}

GET /api/products/{id}/prices

GET /api/products/{id}/history

GET /api/products/{id}/analytics

GET /api/products/{id}/sources

POST /api/tracking

DELETE /api/tracking/{id}

GET /api/health
```

Use Pydantic schemas.

Use proper error responses.

Use async FastAPI endpoints.

---

# 36. FRONTEND

Build a polished dashboard.

Recommended:

* React
* TypeScript
* Tailwind CSS
* Recharts or equivalent charting library

Pages:

```text
/
    Search

/product/:id
    Product dashboard

/tracking
    Tracked products

/settings
    API/provider settings if needed
```

The main product page should feel like a modern analytics dashboard rather than a basic table.

---

# 37. DASHBOARD LAYOUT

Suggested structure:

```text
┌─────────────────────────────────────────────────────────────┐
│ Search                                                     │
│ [ Sony WH-1000XM6                         ] [Analyze]       │
└─────────────────────────────────────────────────────────────┘

Product information

Sony WH-1000XM6
Wireless Noise Cancelling Headphones

───────────────────────────────────────────────────────────────

CURRENT LOWEST      CURRENT AVERAGE      HISTORICAL LOW
₹29,999             ₹31,250              ₹27,499

CURRENT HIGHEST     HISTORICAL AVG       HISTORICAL HIGH
₹33,999             ₹32,850              ₹36,999

───────────────────────────────────────────────────────────────

CURRENT PRICE BY PLATFORM

Amazon          ₹29,999       ↓ 4.2%
Flipkart        ₹30,499       ↓ 2.1%
Croma           ₹31,999       →
Reliance        ₹32,499       ↑ 1.4%

───────────────────────────────────────────────────────────────

PRICE HISTORY

              [7D] [30D] [90D] [6M] [1Y] [ALL]

             Multi-platform price chart

───────────────────────────────────────────────────────────────

AVERAGE PRICE OVER TIME

             Average price chart

───────────────────────────────────────────────────────────────

PRICE STATISTICS

Mean
Median
Min
Max
Volatility
Largest drop
Largest increase

───────────────────────────────────────────────────────────────

HISTORICAL PRICE POSITION

Low ────────────────●──────────────── High

Current price is X% above historical low.

───────────────────────────────────────────────────────────────

DATA SOURCES

Amazon history → Keepa → 12 months
Flipkart history → Own tracker → 14 days
Croma history → unavailable

───────────────────────────────────────────────────────────────

PRODUCT DETAILS

Brand
Model
Variant
Storage
Color
Seller
Availability

───────────────────────────────────────────────────────────────

TRACK THIS PRODUCT

[ Track price ]
```

---

# 38. DO NOT MAKE UNSUPPORTED CLAIMS

The application must clearly distinguish:

### Observed

```text
Current Amazon price: ₹X
```

### Calculated

```text
Average price: ₹Y
```

### Historical observation

```text
Historical low: ₹Z
```

### Inference

```text
Current price is near the lower end of its observed historical range.
```

Do not make unsupported predictions such as:

"Price will definitely fall tomorrow."

If adding a "buy signal" or similar feature later, make it explicitly statistical and explain the methodology. Do not present it as certainty.

For MVP, focus on descriptive analytics rather than predictions.

---

# 39. SECURITY

Never expose API keys to the frontend.

Use environment variables:

```text
SEARCH_API_KEY=
KEEPA_API_KEY=
PRICE_API_KEY=
DATABASE_URL=
```

Create:

```text
.env.example
```

Never commit `.env`.

Validate all external inputs.

Do not execute arbitrary URLs blindly.

Restrict scraping to permitted domains/providers.

---

# 40. PROJECT STRUCTURE

Use a clean structure similar to:

```text
price-intelligence/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   │
│   │   ├── api/
│   │   │   ├── search.py
│   │   │   ├── products.py
│   │   │   ├── history.py
│   │   │   ├── analytics.py
│   │   │   └── tracking.py
│   │   │
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── product_resolver.py
│   │   │   ├── price_aggregator.py
│   │   │   ├── analytics.py
│   │   │   └── search_service.py
│   │   │
│   │   ├── adapters/
│   │   │   ├── base.py
│   │   │   ├── registry.py
│   │   │   ├── amazon.py
│   │   │   ├── flipkart.py
│   │   │   └── ...
│   │   │
│   │   ├── history/
│   │   │   ├── base.py
│   │   │   ├── keepa.py
│   │   │   ├── priceapi.py
│   │   │   └── own_database.py
│   │   │
│   │   ├── workers/
│   │   │   └── tracker.py
│   │   │
│   │   └── db/
│   │
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── types/
│   ├── package.json
│   └── ...
│
├── docker-compose.yml
├── README.md
└── .gitignore
```

You may modify the exact structure if there is a strong engineering reason.

---

# 41. DEVELOPMENT PHASES

Do not attempt to build an enormous production system before establishing a working vertical slice.

Implement in phases.

## Phase 1 — Working vertical slice

Build:

```text
Query
 ↓
Search
 ↓
Find product
 ↓
One ecommerce adapter
 ↓
Current price
 ↓
Dashboard
```

It must actually run.

## Phase 2

Add:

* Multiple ecommerce adapters
* Product matching
* Normalization

## Phase 3

Add:

* External historical providers
* Historical chart
* Historical analytics

## Phase 4

Add:

* Own tracking database
* Scheduler
* Price snapshots

## Phase 5

Add:

* Advanced analytics
* Alerts
* Better caching
* Provider health
* Performance optimization

---

# 42. MOCK / DEMO MODE

The application MUST be runnable even when API keys are unavailable.

Implement a development/demo mode.

Example:

```text
DEMO_MODE=true
```

In demo mode:

* Use realistic mock search results
* Use realistic mock product listings
* Use synthetic but clearly labeled historical data
* Demonstrate all dashboard components

NEVER present synthetic demo data as real data.

Display:

```text
DEMO DATA
```

prominently when demo mode is enabled.

The application should still be architected so replacing the mock provider with a real API requires minimal code changes.

---

# 43. TESTING

Write tests for:

### Unit tests

* Product normalization
* Product matching
* Domain resolution
* Adapter registry
* Price calculations
* Average calculations
* Historical low/high
* Percentage changes
* Missing-data handling

### Integration tests

* Search → product resolution
* Product → adapter
* Adapter → normalized price
* History provider → normalized history
* Dashboard API

### Failure tests

Test:

* Provider timeout
* Invalid URL
* Product not found
* Missing price
* Missing historical data
* Currency mismatch
* Duplicate product
* Wrong variant
* API quota error

---

# 44. OBSERVABILITY

Add structured logging.

For every search:

```text
query
search_provider
results_count
matched_products
adapters_called
providers_called
latency
failures
```

For every price observation:

```text
product
platform
price
timestamp
source
provider
```

Add timing metrics for:

```text
search latency
product matching latency
scraping latency
history API latency
total request latency
```

---

# 45. PERFORMANCE PRINCIPLES

Always prefer:

```text
parallel > sequential
cache > repeated API call
deterministic parsing > LLM
HTTP > browser automation
structured data > HTML scraping
specific identifier > fuzzy title matching
partial result > total failure
```

Do not introduce an LLM call where a simple dictionary lookup or parser is sufficient.

---

# 46. IMPORTANT REAL-WORLD CONSTRAINT

Not every e-commerce website will provide:

* Historical prices
* Public APIs
* Stable HTML
* Easy scraping
* Structured product data

The application must be designed around this reality.

Never fake missing history.

Instead show:

```text
Historical data unavailable

Tracking started today.
```

or:

```text
Historical data available for the last 45 days.
Source: XYZ
```

The dashboard's data provenance must always be visible.

---

# 47. OPTIONAL ADVANCED FEATURES

Architect the code so these can be added later:

### Price alerts

```text
Price < ₹X
Price drops > X%
Price reaches historical low
```

### Wishlist

Users can track products.

### Price-drop notifications

Email / Telegram / push.

### Price-per-unit

For:

* Food
* Cosmetics
* Multipacks
* Household goods

Example:

```text
₹120 / 500ml
₹180 / 1L

Effective comparison:
₹0.24/ml
₹0.18/ml
```

### Coupon detection

If reliably available.

### Cashback

If reliably available.

### Shipping comparison

### Seller reputation

### Availability history

### Stock history

### Price anomaly detection

Detect unusual sudden price changes.

### Product substitution

Show similar products when the requested product isn't available.

---

# 48. IMPORTANT: DO NOT OVERBUILD

This is an MVP.

Do NOT introduce:

* Kubernetes
* Microservices
* Kafka
* Complex event buses
* Multiple databases
* Complex ML models
* Vector databases
* unnecessary cloud infrastructure

unless a real requirement emerges.

Start with:

```text
FastAPI
PostgreSQL
React
TypeScript
Async HTTP
Playwright where necessary
One LLM provider
Search API
One historical provider
A few ecommerce adapters
```

Keep everything modular so infrastructure can be scaled later.

---

# 49. FINAL PRODUCT GOAL

When finished, I should be able to run the application and enter:

```text
Sony WH-1000XM6
```

and get a dashboard that looks conceptually like:

```text
┌───────────────────────────────────────────────────────────┐
│ Sony WH-1000XM6                                           │
│                                                           │
│ LOWEST NOW      AVERAGE NOW       HIGHEST NOW             │
│ ₹29,999         ₹31,250           ₹33,999                │
│                                                           │
│ HISTORICAL LOW  HISTORICAL AVG    HISTORICAL HIGH         │
│ ₹27,499         ₹32,850           ₹36,999                │
├───────────────────────────────────────────────────────────┤
│                                                           │
│ CURRENT PRICES                                            │
│                                                           │
│ Amazon           ₹29,999       History: 12 months         │
│ Flipkart         ₹30,499       History: 30 days           │
│ Croma            ₹31,999       History: unavailable       │
│ Reliance         ₹32,499       History: 90 days           │
│                                                           │
├───────────────────────────────────────────────────────────┤
│                                                           │
│                 PRICE HISTORY                             │
│                                                           │
│       Multi-platform interactive chart                    │
│                                                           │
├───────────────────────────────────────────────────────────┤
│                                                           │
│                 AVERAGE PRICE                             │
│                                                           │
│       Average across available platforms                  │
│                                                           │
├───────────────────────────────────────────────────────────┤
│                                                           │
│ PRICE ANALYTICS                                           │
│                                                           │
│ 7-day change       30-day change       90-day change      │
│ ↓ 3.2%             ↓ 7.1%             ↑ 2.4%             │
│                                                           │
│ Median             Volatility          Largest drop       │
│ ₹31,000            X%                  ₹3,500             │
│                                                           │
├───────────────────────────────────────────────────────────┤
│                                                           │
│ HISTORICAL POSITION                                       │
│                                                           │
│ Low ────────────────●──────────────────── High             │
│                                                           │
│ Current price is X% above historical low.                 │
│                                                           │
├───────────────────────────────────────────────────────────┤
│                                                           │
│ DATA SOURCES                                              │
│                                                           │
│ Amazon → Keepa → 12 months                                │
│ Flipkart → Own tracker → 30 days                          │
│ Croma → No historical data available                      │
│                                                           │
├───────────────────────────────────────────────────────────┤
│                                                           │
│ PRODUCT DETAILS                                           │
│ Brand | Model | Variant | Storage | Color | Seller        │
│                                                           │
├───────────────────────────────────────────────────────────┤
│                                                           │
│ [ Track this product ]                                    │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

---

# 50. IMPLEMENTATION INSTRUCTION

Now build this application.

Do not merely give me an architectural explanation.

Actually create:

1. Complete backend
2. Complete frontend
3. Database models
4. API routes
5. Search abstraction
6. Product-resolution logic
7. Ecommerce adapter abstraction
8. At least 2–3 working adapters/providers where practical
9. Historical-price provider abstraction
10. At least one real historical provider integration where credentials/API access permit
11. Own historical database fallback
12. Analytics calculations
13. Dashboard UI
14. Background tracking architecture
15. Demo/mock mode
16. Tests
17. `.env.example`
18. Docker configuration where useful
19. README with exact setup instructions

If an external API requires credentials that are not available, implement the provider completely behind an interface, provide environment-variable configuration, and provide a working mock implementation so the rest of the application remains functional.

Do not hardcode API keys.

Do not fabricate historical data in production mode.

If a provider cannot provide historical data for a product, clearly return that state.

Prioritize a functioning vertical slice first and then expand it.

At the end, verify that the application can actually start, the backend can respond, the frontend can load, and the demo mode can execute an end-to-end search without requiring external credentials.

Also provide:

* Architecture explanation
* Setup instructions
* Environment variables
* API documentation
* Database schema explanation
* How to add a new ecommerce adapter
* How to add a new historical provider
* How the product matching system works
* How historical data provenance is represented
* Known limitations
* Future improvements
