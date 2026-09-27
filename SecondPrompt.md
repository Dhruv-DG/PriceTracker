# PriceTracker — Phase 2 Implementation Master Prompt

You are working inside the existing GitHub repository:

`https://github.com/Dhruv-DG/PriceTracker`

Do NOT rebuild this project from scratch.

The repository already contains the initial architecture, frontend dashboard, backend services, database models, search provider abstraction, historical-price abstraction, analytics logic, and demo implementations.

Your job now is to turn the existing prototype into a **real, working Unified E-commerce Price Intelligence & Historical Price Dashboard**.

---

# 1. PRIMARY OBJECTIVE

Transform the current implementation from a partially mocked/demo pipeline into a functional system where:

1. User enters a natural-language product query.
2. The system dynamically discovers relevant ecommerce/product results across the web.
3. The system identifies the correct product and variant.
4. The system retrieves current prices from multiple sources.
5. The system retrieves historical prices from legitimate historical-price providers where available.
6. The system stores normalized product/listing/price data in PostgreSQL.
7. The system calculates meaningful price analytics.
8. The frontend displays real data progressively.
9. The user can start tracking a product.
10. Background tracking periodically records new prices.
11. Historical data grows over time when external historical data is unavailable.
12. Every piece of price history clearly indicates its source and coverage.
13. Demo/synthetic data must never be presented as real-world price history.

Do not add unnecessary infrastructure or overengineer the project.

---

# 2. FIRST STEP — INSPECT THE EXISTING REPOSITORY

Before modifying anything:

* Inspect the complete repository structure.
* Read the existing backend and frontend implementation.
* Read `MasterPrompt.md`.
* Identify what is already implemented.
* Identify what is placeholder/demo/mock.
* Identify reusable abstractions.
* Do not duplicate existing functionality.
* Do not replace working components merely because you prefer another architecture.

Create an internal implementation plan based on the actual current code.

Preserve existing functionality wherever possible.

---

# 3. CURRENT ARCHITECTURE TO PRESERVE

The project already has concepts for:

* FastAPI backend
* PostgreSQL / SQLAlchemy models
* Search provider abstraction
* Ecommerce adapter abstraction
* Historical price provider abstraction
* Search orchestration
* Analytics
* Product APIs
* Tracking APIs
* React frontend
* Price history charts
* Dashboard analytics
* Demo mode

Build on these.

Do NOT convert the project into:

* Kubernetes
* Kafka
* microservices
* vector databases
* distributed workers
* unnecessary event buses
* complex cloud infrastructure

The goal is a strong, production-style individual project, not enterprise infrastructure for its own sake.

---

# 4. CRITICAL PROBLEMS TO FIX

Implement the following in priority order.

---

## PHASE A — REAL DATA PIPELINE

The most important requirement is that the application actually works with real product data.

The pipeline should become:

```text
User Query
   ↓
Query Understanding
   ↓
Search Provider
   ↓
Candidate Results
   ↓
URL Normalization
   ↓
Ecommerce Detection
   ↓
Product Extraction
   ↓
Product / Variant Matching
   ↓
Canonical Product
   ↓
Current Price Retrieval
   ↓
Historical Price Retrieval
   ↓
Normalization
   ↓
PostgreSQL Persistence
   ↓
Analytics
   ↓
Dashboard
```

Do not allow demo history to remain the default path when live mode is enabled.

---

# 5. HISTORICAL PRICE PROVIDER SYSTEM

The repository already contains a historical provider abstraction.

Make it real.

Create a provider registry such as:

```python
HistoricalProviderRegistry
```

with providers implementing a common interface such as:

```python
class HistoricalPriceProvider(ABC):

    @abstractmethod
    async def get_history(
        self,
        product_identifier: ProductIdentifier
    ) -> HistoricalPriceResult:
        ...
```

The result should normalize to something similar to:

```python
HistoricalPriceResult(
    provider=...,
    product_id=...,
    currency=...,
    observations=[...],
    coverage_start=...,
    coverage_end=...,
    confidence=...,
    source_url=...
)
```

---

# 6. KEEPA INTEGRATION

The configuration already contains a Keepa API key concept.

If the existing project targets Amazon products:

* Implement a proper Keepa provider.
* Do not fake Keepa data.
* Do not label synthetic data as Keepa.
* Use the correct Amazon identifier where possible, such as ASIN.
* Normalize Keepa historical observations into the application's common schema.
* Handle API errors.
* Handle missing products.
* Handle API quota/rate-limit failures.
* Handle missing historical data.

If Keepa cannot be used for a particular product, gracefully fall back to another provider or own tracking.

Keep the provider isolated behind the historical provider interface.

Do not couple the entire application to Keepa.

---

# 7. OTHER HISTORICAL PROVIDERS

Design the system so additional legitimate historical data providers can be added without changing the main search pipeline.

For example:

```text
HistoricalProviderRegistry
    ├── KeepaProvider
    ├── OtherHistoricalProvider
    └── OwnTrackingProvider
```

Only implement providers that can actually be used through legitimate APIs/data sources.

Do NOT scrape competing price-history websites simply because they display historical data.

Do not bypass:

* CAPTCHA
* authentication
* paywalls
* anti-bot protections

---

# 8. OWN PRICE HISTORY

The system must maintain its own historical data.

Whenever a product listing is known:

```text
ProductListing
      ↓
Current Price Fetch
      ↓
PriceObservation
```

Store:

* timestamp
* price
* currency
* shipping price if known
* availability
* source
* seller
* platform
* listing URL
* extraction method

This allows the application to build its own history over time.

---

# 9. CANONICAL PRODUCT IDENTITY

Fix the current product identity problem.

A search query itself must NOT become the permanent product identity.

For example:

```text
"iphone 17 256gb black"
"Apple iPhone 17 256 GB Black"
"iphone17 black 256"
```

should resolve to the same canonical product when appropriate.

Create or properly use:

```text
Product
ProductVariant
ProductListing
```

or equivalent existing models.

Use identifiers such as:

* ASIN
* GTIN
* UPC
* EAN
* MPN
* SKU
* manufacturer model number

when available.

Variant matching must consider:

* storage
* RAM
* color
* size
* generation
* model
* connectivity
* condition
* region
* bundle
* other meaningful variant attributes

Do not merge different variants.

---

# 10. PRODUCT MATCHING

The current pipeline must not assume that every search result is the requested product.

Implement:

```text
Candidate Discovery
        ↓
Deterministic Filtering
        ↓
Product Attribute Extraction
        ↓
Product Matching
        ↓
Confidence Score
        ↓
Accepted / Rejected
```

Use deterministic matching first.

Use an LLM only when ambiguity remains.

The LLM should receive structured candidate information rather than entire webpages whenever possible.

Example:

```json
{
  "requested_product": {
    "brand": "Apple",
    "model": "iPhone 17",
    "storage": "256GB",
    "color": "Black"
  },
  "candidate": {
    "title": "...",
    "brand": "...",
    "model": "...",
    "storage": "...",
    "color": "..."
  }
}
```

The LLM should return structured output.

Do not use an LLM for every simple filtering operation.

---

# 11. SEARCH PROVIDER

Keep the search provider abstract.

The system should support something like:

```python
class SearchProvider:
    async def search(query: str) -> SearchResults:
        ...
```

Continue using the existing provider where appropriate.

Exploit shopping/search results when available because they can provide:

* product title
* current price
* URL
* merchant
* image
* source

Use those results for fast initial discovery.

Do not blindly scrape every search result.

---

# 12. SEARCH PIPELINE PERFORMANCE

The current search implementation should not perform expensive LLM calls sequentially for every candidate.

Change the flow to:

```text
Search
 ↓
Deterministic filtering
 ↓
Deduplication
 ↓
Parallel candidate processing
 ↓
LLM only for ambiguous candidates
```

Use async concurrency carefully.

For example:

```python
asyncio.gather(...)
```

where appropriate.

Do not create uncontrolled concurrency that can trigger provider rate limits.

---

# 13. ECOMMERCE ADAPTER SYSTEM

The existing adapter abstraction should become an actual registry.

Example:

```python
EcommerceAdapterRegistry
```

with:

```text
AmazonAdapter
FlipkartAdapter
CromaAdapter
OtherSupportedAdapter
GenericAdapter
```

Do NOT hardcode a fixed list of stores into the entire application.

The architecture must remain extensible.

Use:

```python
can_handle(url)
extract_product(url)
get_current_price(url)
get_availability(url)
get_product_details(url)
```

or the equivalent existing interface.

---

# 14. GENERIC ADAPTER

Keep the GenericAdapter as a fallback.

Extraction priority should be:

```text
Official API
↓
JSON-LD / Schema.org
↓
Structured metadata
↓
Stable HTML selectors
↓
Browser automation
↓
LLM fallback
```

Do not use browser automation unless necessary.

Do not use LLM extraction for straightforward JSON-LD data.

---

# 15. MARKETPLACE SELLERS

Do not treat:

```text
Platform
```

and:

```text
Seller
```

as the same thing.

For marketplace products, represent:

```text
Platform = Amazon
Seller = Seller A
```

and:

```text
Platform = Amazon
Seller = Seller B
```

as separate offers/listings when appropriate.

This is necessary for meaningful price comparisons.

---

# 16. PRICE MODEL

Separate:

```text
listed_price
shipping_price
effective_price
currency
```

Do NOT assume:

```text
unknown shipping = ₹0
```

If shipping is unknown:

```text
effective_price = unknown
```

unless there is a clearly documented reason to calculate it differently.

The UI should distinguish:

* product price
* shipping
* effective price
* unknown shipping

---

# 17. DATABASE AS SOURCE OF TRUTH

Make PostgreSQL the real source of truth.

Use existing models where possible.

At minimum, properly persist:

```text
products
product_listings
platforms
price_observations
historical_sources
searches
search_results
tracking_jobs
price_alerts
```

Do not create a new database architecture unless the existing one is fundamentally unusable.

---

# 18. DATABASE MIGRATIONS

Do not rely on:

```python
Base.metadata.create_all()
```

as the long-term migration mechanism.

If Alembic is not already configured:

* configure Alembic
* create an initial migration
* create migrations for schema changes

The application must be able to initialize a fresh database predictably.

Document:

```bash
alembic upgrade head
```

and the required setup process.

---

# 19. PRODUCT API

Implement the currently placeholder endpoints.

For example:

```text
GET /api/products/{product_id}
GET /api/products/{product_id}/prices
GET /api/products/{product_id}/history
GET /api/products/{product_id}/analytics
```

These endpoints must read from real persisted data.

Do not return:

```json
{
  "status": "not_implemented_yet"
}
```

or empty placeholder structures.

---

# 20. SEARCH API

The search endpoint should return enough information for the dashboard.

Example structure:

```json
{
  "product": {...},
  "listings": [...],
  "current_prices": [...],
  "history": [...],
  "analytics": {...},
  "data_coverage": {...}
}
```

Do not expose internal implementation details unnecessarily.

---

# 21. PROGRESSIVE LOADING

The frontend should not wait for every historical source before showing current prices.

Use staged loading:

```text
Stage 1:
Search results / current prices

Stage 2:
Verified product information

Stage 3:
Historical data

Stage 4:
Analytics

Stage 5:
Tracking availability
```

If practical, implement this using:

* separate API calls
* polling
* SSE

Do not use fake `setTimeout()` progress indicators to pretend work is happening.

Actual backend state should drive progress.

---

# 22. ANALYTICS — IMPORTANT

Review the existing analytics implementation carefully.

Do not blindly trust the current formulas.

Implement these metrics correctly.

---

## Current Price

For each platform/listing:

```text
Current Price
```

---

## Current Lowest

Minimum valid current listed/effective price.

---

## Current Highest

Maximum valid current listed/effective price.

---

## Current Cross-Platform Average

Average current price across valid platforms/listings.

Clearly define whether multiple sellers from one platform are included.

---

## Historical Low

Minimum historical observed price.

Show:

```text
overall historical low
platform-specific historical low
```

where data exists.

---

## Historical High

Maximum historical observed price.

---

## Historical Average

Calculate carefully.

Support:

```text
Observation-weighted average
```

and preferably:

```text
Platform-balanced average
```

Do not let a platform with 10,000 observations dominate a platform with 20 observations without making that distinction explicit.

---

# 23. AVERAGE PRICE OVER TIME

For each date/time bucket:

```text
average_price
contributing_platform_count
observation_count
```

If only two platforms have data on a particular date, do not pretend five platforms contributed.

Expose coverage information to the frontend.

---

# 24. PRICE VOLATILITY

Do NOT define volatility merely as:

```text
standard_deviation(price) / mean(price)
```

That is price dispersion, not necessarily time-series volatility.

Implement time-series volatility using percentage changes where enough observations exist.

For example:

```text
daily percentage change
→ standard deviation of percentage changes
```

Also optionally expose:

```text
price dispersion
```

as a separate metric.

---

# 25. PRICE MOVEMENTS

If calculating:

```text
largest drop
largest increase
```

calculate the change relative to the previous observation:

```text
(current - previous) / previous
```

Do not compare every observation against the historical average.

---

# 26. PLATFORM CONSISTENCY

If showing something like:

```text
Most consistent platform
```

define it mathematically.

Prefer a normalized measure such as:

```text
coefficient of variation
```

or:

```text
percentage-change volatility
```

Do not use raw price variance across platforms with different price levels.

Rename the metric if necessary to something less ambiguous, such as:

```text
Lowest price variability
```

---

# 27. PRICE POSITION

Calculate where the current price sits relative to historical range.

Example:

```text
Historical Low
      ↓
Current Price
      ↓
Historical Average
      ↓
Historical High
```

Expose a normalized position where possible.

Example:

```text
(current - historical_low)
/
(historical_high - historical_low)
```

Handle the zero-range case safely.

---

# 28. DATA COVERAGE

Add a first-class data coverage concept.

For every source/platform, show:

```text
Source
History available?
Coverage start
Coverage end
Number of observations
Last updated
Source type
Confidence
```

Example:

```text
Amazon
History: 2 years
Observations: 1,284
Last updated: 5 minutes ago
Source: Keepa
```

versus:

```text
Flipkart
History: 14 days
Observations: 14
Source: Own Tracker
```

This is extremely important because historical coverage will differ between platforms.

---

# 29. OWN TRACKING

Implement the tracking API properly.

For example:

```text
POST /api/tracking
GET /api/tracking
DELETE /api/tracking/{id}
```

Starting tracking should create a real:

```text
TrackingJob
```

in the database.

It should contain information such as:

```text
product_id
listing_id
frequency
status
last_run
next_run
created_at
```

---

# 30. BACKGROUND TRACKER

Implement a lightweight scheduler suitable for the project.

It should:

1. Load active tracking jobs.
2. Fetch current prices.
3. Store price observations.
4. Detect changes.
5. Update next execution time.

Keep the implementation simple.

A lightweight scheduler/background worker is sufficient.

Do not introduce Celery/Kafka/etc. unless the existing architecture truly requires it.

---

# 31. PRICE ALERTS

If the existing model/API supports alerts, implement a basic version.

Examples:

```text
Alert when price <= ₹X
Alert when price drops by X%
Alert when price reaches historical low
```

Store alert configuration.

Do not implement notifications that require external services unless credentials are available.

At minimum, record triggered alerts.

---

# 32. CACHE

The existing in-memory cache is acceptable for local development.

Improve the abstraction so Redis can later replace it.

Example:

```text
CacheBackend
    ├── MemoryCache
    └── RedisCache
```

Do not make Redis mandatory for local development.

Cache:

* identical searches
* product metadata
* expensive historical API responses
* possibly current price data for a short TTL

Do not cache stale prices indefinitely.

---

# 33. DEMO MODE

Keep demo mode, but make it explicit.

Example environment variable:

```env
DEMO_MODE=false
```

When:

```env
DEMO_MODE=true
```

the application may use synthetic/demo providers.

However:

* clearly label demo data
* never call synthetic data "real"
* never label synthetic data as actual Keepa data
* show "Demo Data" in the UI

Production/live mode must use real providers.

---

# 34. FRONTEND

Keep the current dashboard design where useful.

Improve it to consume real backend APIs.

The dashboard should contain:

### Header

Product name and variant.

### Current Price Summary

* Lowest current price
* Highest current price
* Current average
* Historical low
* Historical average
* Price position

### Current Offers

Columns:

```text
Platform
Seller
Current Price
Shipping
Effective Price
Availability
Last Updated
```

### Historical Price Chart

Multiple platform lines.

Support:

```text
7D
30D
90D
6M
1Y
ALL
```

Only display ranges for which data exists.

### Average Price Over Time

Show:

```text
Average price
Contributing platforms
```

### Analytics

Include:

* current vs historical average
* historical low/high
* recent price changes
* volatility
* price dispersion
* price position

### Data Coverage

Show exactly where the history came from.

### Product Details

Show:

* brand
* model
* variant
* specifications
* identifiers
* images where available

### Tracking

Allow the user to:

```text
Track Product
```

and configure tracking/alerts.

---

# 35. FRONTEND API CONFIGURATION

Do NOT hardcode:

```text
http://localhost:8000/api
```

Use an environment variable such as:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

Provide:

```text
.env.example
```

---

# 36. ROUTING

If practical, structure the frontend into:

```text
/
    Search

/product/:id
    Product Dashboard

/tracked
    Tracked Products

/settings
    Settings
```

Do not overcomplicate routing if the current frontend architecture makes a simpler approach preferable.

---

# 37. FRONTEND ERROR STATES

Handle:

* no results
* product not found
* API failure
* provider failure
* historical data unavailable
* partial data
* rate limit
* invalid query
* no current price
* no historical data

Do not show a blank dashboard.

Explain partial data clearly.

---

# 38. PERFORMANCE TARGET

Aim for:

```text
Query parsing:
<500 ms where possible

Search/discovery:
~1–3 seconds

Current price retrieval:
~1–5 seconds depending on sources

Initial dashboard:
~5 seconds where practical
```

Do not sacrifice correctness for artificial benchmark numbers.

Parallelize independent network requests.

Cache expensive operations.

Avoid unnecessary LLM calls.

---

# 39. LLM RESPONSIBILITIES

LLM should be used for:

### Query understanding

Example:

```text
"iphone 17 black 256"
```

→

```json
{
  "brand": "Apple",
  "model": "iPhone 17",
  "storage": "256GB",
  "color": "Black"
}
```

### Ambiguous product matching

### Difficult semantic classification

LLM should NOT be used for:

* URL domain detection
* basic price extraction from JSON-LD
* simple HTML parsing
* routing to an adapter
* straightforward deterministic filtering

---

# 40. SECURITY

Do not expose API keys to the frontend.

All external provider credentials must remain server-side.

Use environment variables.

Validate URLs.

Validate query parameters.

Prevent arbitrary internal network access if URL fetching is user-controlled.

Add reasonable timeouts.

Handle provider failures safely.

---

# 41. OBSERVABILITY

Add useful structured logging around:

```text
search_started
search_completed
candidate_count
candidate_matched
price_fetch_started
price_fetch_completed
history_provider_used
history_provider_failed
database_write
tracking_run
```

Do not log:

* API keys
* secrets
* sensitive tokens

---

# 42. TESTING

Add or improve tests for:

### Query parsing

```text
iPhone 17 256GB Black
Sony WH-1000XM6
Nike Air Max 270 size 9
```

### Product matching

Different variants must not accidentally merge.

### Price normalization

Test:

```text
₹99,999
99,999 INR
$999
```

appropriately.

### Shipping

Unknown shipping must not become zero.

### Analytics

Test:

* average
* low
* high
* volatility
* percentage changes
* price position
* platform coverage

### Historical providers

Mock provider responses.

### API

Test:

```text
search
product
history
analytics
tracking
```

### Tracking

Ensure jobs create actual DB records.

---

# 43. DATABASE TEST

The system should work against a clean database.

Document the exact setup:

```bash
# install dependencies
# configure .env
# create database
# run migrations
# start backend
# start frontend
```

A new developer should be able to clone the repository and understand how to run it.

---

# 44. README

Update the README with:

## Project Overview

What PriceTracker does.

## Architecture

Show:

```text
Frontend
   ↓
FastAPI
   ↓
Search Provider
   ↓
Product Resolution
   ↓
Ecommerce Adapters
   ↓
Historical Providers
   ↓
PostgreSQL
   ↓
Analytics
```

## Setup

Exact commands.

## Environment Variables

Document:

```text
DATABASE_URL
SEARCH_API_KEY
LLM_API_KEY
KEEPA_API_KEY
DEMO_MODE
VITE_API_BASE_URL
```

Only include variables that actually exist in the implementation.

## Running

Backend command.

Frontend command.

## Demo Mode

Explain clearly.

## Live Providers

Explain which providers require API keys.

---

# 45. IMPORTANT IMPLEMENTATION RULES

Follow these rules throughout implementation.

### Rule 1

Do not rewrite the project from scratch.

### Rule 2

Inspect before modifying.

### Rule 3

Reuse existing abstractions.

### Rule 4

Replace placeholders with real implementations.

### Rule 5

Do not fake live data.

### Rule 6

Do not label synthetic data as historical provider data.

### Rule 7

Do not use LLMs for deterministic tasks.

### Rule 8

Do not make Redis mandatory.

### Rule 9

Do not introduce unnecessary infrastructure.

### Rule 10

Do not bypass anti-bot systems.

### Rule 11

Do not silently merge different product variants.

### Rule 12

Persist real observations in PostgreSQL.

### Rule 13

Analytics must have mathematically meaningful definitions.

### Rule 14

Partial data is acceptable, but it must be explicitly communicated.

### Rule 15

Correctness is more important than adding more UI features.

---

# 46. IMPLEMENTATION ORDER

Implement in this exact general order:

```text
1. Repository inspection
2. Database/migration verification
3. Canonical product + listing persistence
4. Product matching
5. Ecommerce adapter registry
6. Real current-price pipeline
7. Historical provider registry
8. Keepa integration
9. Own price observation storage
10. Correct analytics
11. Product/history/analytics APIs
12. Tracking jobs
13. Background price tracking
14. Frontend integration
15. Progressive loading
16. Error states
17. Tests
18. README/documentation
19. Final end-to-end verification
```

Do not spend most of the time polishing UI before steps 1–13 work.

---

# 47. ACCEPTANCE CRITERIA

The implementation is considered successful only when the following flow works:

User enters:

```text
iPhone 17 256GB Black
```

The system should:

```text
1. Understand the query.

2. Search the web/shopping provider.

3. Discover relevant product candidates.

4. Remove irrelevant results.

5. Identify the correct product/variant.

6. Identify available ecommerce listings.

7. Retrieve current prices.

8. Persist product/listing/current price information.

9. Retrieve historical data when an external provider supports it.

10. Fall back to own tracking history when external history is unavailable.

11. Normalize all observations.

12. Calculate:
    - current lowest
    - current highest
    - current average
    - historical low
    - historical high
    - historical average
    - recent price movement
    - volatility
    - price position

13. Return the data through APIs.

14. Render the dashboard.

15. Clearly show source and historical coverage.

16. Allow tracking to be enabled.

17. Create a real tracking job.

18. Store future price observations.
```

---

# 48. DO NOT DECLARE SUCCESS PREMATURELY

After implementation, actually test the complete flow.

Do not say:

> "Implemented successfully"

merely because the application compiles.

Verify:

```text
Search
→ Product resolution
→ Current prices
→ History
→ Database persistence
→ Analytics
→ API
→ Frontend
→ Tracking
```

If external APIs are unavailable because credentials are missing, clearly identify exactly which part could not be verified.

Use demo mode only for components that genuinely cannot be tested without external credentials.

---

# 49. FINAL DELIVERABLE

At the end, provide a concise implementation report containing:

### Implemented

List the actual features completed.

### Files Changed

List important files changed and why.

### Database Changes

List schema/migration changes.

### APIs Added/Modified

List endpoints.

### Providers

List real providers implemented and which require credentials.

### Remaining Limitations

Be honest.

### How To Run

Exact commands.

### How To Test

Give an end-to-end test procedure.

### Known Issues

List anything that could not be verified.

---

# FINAL INSTRUCTION

Start by inspecting the existing repository thoroughly.

Do not ask me to manually describe code that you can inspect yourself.

Do not generate a new project.

Do not delete working components just to replace them with your preferred architecture.

Make incremental changes to the existing PriceTracker repository.

Prioritize:

**real data → correct product identity → real persistence → real historical data → correct analytics → tracking → frontend integration → polish.**

The final result should be a genuinely functional price-intelligence application rather than a UI demo.
