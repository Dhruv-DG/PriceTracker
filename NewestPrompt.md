# PRICE TRACKER — MASTER IMPLEMENTATION PROMPT
## Correct Discovery, Scraping Independence, Minimal Price Data, Historical Integrity & Analytics

You are Claude Opus acting as the senior engineer responsible for modifying an existing production-style repository.

Repository:
https://github.com/Dhruv-DG/PriceTracker

Branch:
main

---

# 0. ABSOLUTE RULE — INSPECT THE CURRENT REPOSITORY FIRST

Before changing ANYTHING:

1. Inspect the complete current repository.
2. Read the relevant backend and frontend files.
3. Understand the existing architecture and current implementation.
4. Do NOT rebuild the application from scratch.
5. Do NOT assume the code is in the same state as previous prompts.
6. Treat the current repository as the source of truth.
7. Identify what is already implemented and modify it rather than duplicating functionality.
8. Run the existing tests before making changes.
9. After implementation, run the tests again.

Important:

This is a correction/refinement task, NOT a request to redesign the entire application.

Do not introduce unrelated features.

---

# 1. CORE PRODUCT PRINCIPLE

The most important principle of PriceTracker is:

## SEARCH DISCOVERY ≠ PRICE VERIFICATION

These are two separate operations.

The search engine discovers potentially relevant products/listings.

The scraper/adapter attempts to verify and extract information from those discovered URLs.

A scraping failure MUST NEVER cause a discovered result to disappear.

Example:

Serper discovers:

Amazon:
https://amazon.in/...

Flipkart:
https://flipkart.com/...

Croma:
https://croma.com/...

Suppose:

Amazon scraper succeeds.
Flipkart scraper fails.
Croma scraper times out.

The final result MUST still contain:

Amazon → verified price
Flipkart → link discovered, price unavailable/unverified
Croma → link discovered, price unavailable/unverified

NOT:

Amazon → shown
Flipkart → removed
Croma → removed

The user specifically wants the links discovered by search to remain available.

---

# 2. DISCOVERY RESULT MUST SURVIVE SCRAPING FAILURE

Current/target behavior:

Every valid discovered product result should have a lifecycle similar to:

DISCOVERED
    ↓
CLASSIFIED / FILTERED
    ↓
PROVISIONAL INFORMATION
    ↓
SCRAPE ATTEMPT
    ↓
┌───────────────────────────────┐
│                               │
SUCCESS                         FAILURE
│                               │
VERIFIED                        UNVERIFIED
│                               │
PRICE AVAILABLE                 LINK STILL AVAILABLE
│                               │
└───────────────┬───────────────┘
                ↓
             DISPLAY

A scraper failure must NOT mutate:

is_product_page = false

and must NOT delete the result.

It must only affect verification/extraction state.

---

# 3. SEARCH DISCOVERY IS THE SOURCE OF MARKET OPTIONS

The search pipeline should prioritize finding the market.

Do not make the application overly dependent on successful scraping.

If a search provider finds a relevant product URL and the result passes product relevance filtering:

KEEP IT.

Even if:

- page returns 403
- page returns 429
- request times out
- HTML structure changed
- JSON-LD missing
- price selector missing
- adapter fails
- anti-bot blocks the request
- network error occurs
- parser throws an exception

The result should remain visible.

The UI can show:

"Price unavailable"

or

"Unable to verify price"

with the discovered product link.

---

# 4. DO NOT CONFUSE THESE STATES

Maintain a clear distinction between:

### Discovery state

Was a potentially relevant product/listing discovered?

### Verification state

Was the product/page successfully accessed and verified?

### Price state

Was a usable price extracted?

These are NOT the same thing.

For example:

{
    "url": "...",
    "platform": "Flipkart",
    "title": "Samsung Galaxy S26 Ultra...",
    "discovered": true,
    "product_match": true,
    "verification_status": "FAILED",
    "price": null
}

This is a VALID result.

It should appear in the dashboard.

---

# 5. REQUIRED MINIMAL PRICE TABLE

The product-price comparison table should be simplified.

REMOVE these columns completely:

- MRP
- Discount
- Shipping
- Seller

Do not merely hide them in the frontend while retaining unnecessary UI complexity.

Remove their use from the price comparison response/UI where they are not needed.

The core columns should be approximately:

| Platform | Product / Listing | Price | Status | Link |
|----------|------------------|-------|--------|------|

You may adjust exact naming to fit the existing design.

For example:

Amazon | Samsung Galaxy S26 Ultra | ₹1,39,999 | Verified | View
Flipkart | Samsung Galaxy S26 Ultra | ₹1,30,999 | Verified | View
Croma | Samsung Galaxy S26 Ultra | — | Unverified | View
Reliance Digital | Samsung Galaxy S26 Ultra | — | Unverified | View

The link MUST remain available regardless of price extraction success.

---

# 6. PRICE DISPLAY RULES

There are only two fundamentally different price situations.

## VERIFIED PRICE

If an adapter successfully extracts and validates a price:

Display:

₹1,39,999
Verified

This price can participate in current-price analytics.

---

## UNVERIFIED / FAILED PRICE

If scraping fails:

Display:

Price unavailable
Unverified

or equivalent.

DO NOT invent a price.

DO NOT silently use a stale value.

DO NOT treat a failed scrape as price = 0.

DO NOT treat a missing price as a valid current market price.

The product link must still be displayed.

---

# 7. VERY IMPORTANT — PROVISIONAL SEARCH PRICES

The search engine may provide price metadata.

For example:

Serper Shopping result:

{
    "price": "₹1,30,999",
    "source": "Flipkart",
    "link": "...",
    ...
}

This can be useful as a DISCOVERY/PROVISIONAL price.

However:

A search-engine-derived price is NOT automatically a verified scraped price.

Maintain the distinction.

For example:

search_price = 130999
verified_price = null
verification_status = "FAILED"

The application may display the discovered price only if it is clearly labelled as:

"Search price"
"Discovered price"
"Unverified"

depending on the final UX.

But it must NOT be treated as a verified observation.

---

# 8. CRITICAL HISTORICAL DATA INTEGRITY RULE

This is one of the most important changes.

NEVER persist an unverified/provisional search-engine price into the application's own historical price database as if it were a verified observation.

Currently the architecture has the potential to pass provisional prices through the enrichment flow.

Fix this.

For example:

INVALID:

PriceData:
    price = 130999
    verification_status = FAILED
    source = serper

Then:

PriceObservation:
    price = 130999
    source_type = OWN_TRACKER
    confidence = 1.0

This MUST NOT happen.

---

# 9. WHAT MAY ENTER OWN HISTORICAL DATA

Only prices that satisfy the application's defined historical-data quality requirements should be persisted.

At minimum:

verification_status == VERIFIED

AND

price > 0

AND

the result corresponds to a valid product/listing.

The historical observation must retain provenance.

For example:

source = "live_search"
source_type = "OWN_TRACKER"
provider = actual extraction provider / adapter

Do NOT claim confidence=1.0 merely because an extraction succeeded.

Use a meaningful confidence model if one already exists.

---

# 10. DISCOVERY DATA AND HISTORICAL DATA ARE DIFFERENT DATASETS

Conceptually maintain:

## Discovery Dataset

What the search engine found RIGHT NOW.

Can contain:

- unverified URLs
- missing prices
- provisional prices
- products that could not be scraped

Purpose:

MARKET DISCOVERY.

---

## Current Verified Dataset

What the application successfully verified RIGHT NOW.

Contains:

- verified product
- verified price

Purpose:

CURRENT PRICE COMPARISON.

---

## Historical Dataset

What the application has legitimately recorded over time.

Contains only quality-controlled observations.

Purpose:

PRICE HISTORY / ANALYTICS.

Do not mix these datasets.

---

# 11. CURRENT PRICE ANALYTICS

Current price analytics should use VERIFIED prices only.

For example:

Current Lowest
Current Average
Current Highest

must be calculated only from:

verification_status == VERIFIED

and:

effective_price > 0

Do NOT include:

- failed scrape prices
- provisional search prices
- missing prices
- stale prices
- zero prices

If no verified prices exist:

display an appropriate "No verified price available" state.

Do NOT calculate fake averages.

---

# 12. CURRENT VS HISTORICAL AVERAGE BUG

Audit the existing analytics implementation carefully.

If a metric is called:

"VS Historical Average"

then it must actually compare:

CURRENT VERIFIED AVERAGE

against

HISTORICAL AVERAGE

unless the UI is explicitly renamed to describe another metric.

Do NOT compare:

current lowest

against

historical average

while labelling the result as current average vs historical average.

Use mathematically consistent naming.

For example:

percentage_difference =
    ((current_average - historical_average)
     / historical_average) * 100

Handle zero/null historical values safely.

---

# 13. HISTORICAL DATA QUALITY

Historical data should not blindly be treated as trustworthy.

Before using observations for analytics, validate:

- price > 0
- valid timestamp
- valid platform/listing
- reasonable confidence
- valid source
- no obvious corrupt values

Do not silently delete valid historical observations merely because they are unusual.

An unusually low/high price can be legitimate.

Instead, distinguish:

VALID BUT EXTREME

from

INVALID/CORRUPT

For example:

₹2,619 for a ₹1.4 lakh phone may be suspicious.

Do not automatically assume it is real.

The system should be able to flag or exclude obviously corrupted observations from analytics without destroying the raw record.

---

# 14. OUTLIER HANDLING

Introduce a clear separation between:

RAW OBSERVATIONS

and

ANALYTICS-ELIGIBLE OBSERVATIONS

If an observation appears to be an obvious anomaly:

- retain the raw observation
- mark/flag it if appropriate
- exclude it from derived analytics when justified

Do not permanently delete raw historical data simply because it is an outlier.

Document the rule.

Avoid arbitrary hardcoded product-specific thresholds.

Prefer robust statistical/data-quality logic where appropriate.

---

# 15. HISTORICAL AVERAGE WEIGHTING

Audit how historical averages are currently calculated.

Do not let a platform with thousands of observations automatically dominate another platform that has only a few observations if the metric is intended to describe the market across platforms.

Clearly distinguish:

### Observation-weighted average

Every observation has equal weight.

from:

### Platform-balanced average

Each platform contributes equally.

Choose the appropriate semantics for each dashboard metric and document them.

Do not silently mix the two.

For example:

Historical Market Average

should have a clearly defined methodology.

---

# 16. MULTIPLE LISTINGS PER PLATFORM

IMPORTANT.

Do NOT deduplicate search results merely because they belong to the same domain.

The current implementation contains domain-level deduplication logic such as:

seen_domains

This is too aggressive.

Example:

Amazon result A
Amazon result B
Amazon result C

These may represent:

- different sellers
- different listings
- different variants
- different URLs
- different offers

All potentially useful market options.

Therefore:

REMOVE DOMAIN-LEVEL DEDUPLICATION.

Keep exact URL deduplication.

Correct:

same URL → remove duplicate

different URLs on same platform → preserve

This is especially important because the product is supposed to discover the market rather than reduce it to one arbitrary result per website.

---

# 17. PLATFORM GROUPING

The frontend may group results visually by platform.

But grouping is NOT deduplication.

Example:

Amazon
    Listing 1
    Listing 2
    Listing 3

Flipkart
    Listing 1
    Listing 2

This is valid.

If only one result is ultimately shown as "current cheapest", that is an analytics decision, not a reason to discard other discovered listings.

---

# 18. PRODUCT RELEVANCE FILTERING

Continue filtering out clearly irrelevant search results:

- reviews
- news
- blogs
- forums
- unrelated articles
- unrelated products

However:

Do NOT filter a result merely because scraping failed.

Correct:

Relevant product + scraper failed
→ KEEP

Irrelevant page + scraper succeeds
→ REMOVE

This distinction is fundamental.

---

# 19. LLM RESPONSIBILITY

Keep the LLM focused on semantic classification.

The LLM should answer questions such as:

- Is this result relevant to the requested product?
- Is this likely a product page?
- Does the result match the requested model/variant?

It should NOT be responsible for determining whether a page survives after scraping.

A failed scraper is not evidence of irrelevance.

---

# 20. SEARCH RESULT PERSISTENCE

Audit the Search and SearchResult models.

Ensure discovered candidates can be persisted or represented sufficiently for status retrieval.

The search should retain:

- URL
- title
- domain/platform
- relevance/classification
- product-page classification
- discovery source
- provisional/search price if available
- verification status
- extracted verified price if available
- failure reason if applicable

Do not make the frontend dependent on a successful scraper response for a URL to exist.

---

# 21. FAILURE STATES

Use explicit failure states.

Examples:

DISCOVERED
CLASSIFIED
VERIFYING
VERIFIED
UNVERIFIED
FAILED

Do not overload one field to represent all of these concepts if that creates ambiguity.

At minimum, distinguish:

"not scraped"

from

"scrape failed"

from

"scraped successfully but no price found"

from

"verified price found"

The exact enum design is up to you after inspecting the existing schemas.

Do not introduce unnecessary complexity.

---

# 22. LINKS ARE FIRST-CLASS DATA

Every retained discovery result should have a valid external URL.

The frontend must allow the user to open it.

For failed scraping:

[View Product]

must still work.

Do not disable or remove the link because the price is unavailable.

Use safe external-link handling.

---

# 23. SHIPPING / MRP / DISCOUNT / SELLER REMOVAL

The application does not need these fields in the primary price-comparison experience.

Remove from:

- price table
- dashboard cards where unnecessary
- response models where they are not required
- frontend rendering
- analytics logic

Specifically remove/stop surfacing:

MRP
Discount
Shipping
Seller

Do not leave dead UI fields pretending to be useful.

However:

Before deleting database fields or breaking existing models/migrations, inspect how they are used.

Do not perform destructive schema changes unnecessarily.

If a field is still required internally by an adapter, it may remain internally.

The requirement is that these are NOT part of the core user-facing price comparison model.

---

# 24. EFFECTIVE PRICE

Audit the existing concept of:

effective_price

There is currently a potential semantic problem where:

shipping = None

can effectively behave like:

shipping = 0

This is misleading.

Since shipping is no longer part of the core product UI, avoid allowing unknown shipping to contaminate the core price metric.

For this project, unless there is a clearly defined shipping-inclusive price:

effective price should not pretend that unknown shipping equals zero.

Prefer the actual listed price as the current price.

If shipping is unknown, the system should not fabricate an adjusted total.

---

# 25. CURRENT PRICE MODEL

The clean conceptual model should be:

discovered_price
    ↓
verified_price

with:

price_status

Example:

{
    "discovered_price": 139999,
    "verified_price": null,
    "price_status": "UNVERIFIED"
}

or, after successful extraction:

{
    "discovered_price": 139999,
    "verified_price": 139999,
    "price_status": "VERIFIED"
}

Do not collapse these into one ambiguous `price` field if doing so makes provenance unclear.

Adapt to the existing schema rather than unnecessarily rewriting everything.

---

# 26. HISTORICAL PROVIDER FALLBACK

Audit the historical provider registry.

Current architecture selects an available provider.

But there is an important distinction:

Provider unavailable

vs.

Provider available but returned no usable history.

Example:

Keepa is available for Amazon.

Keepa returns no observations.

The system should be able to fall back to the own database when appropriate.

Do not only fall back when the provider itself is unavailable.

Implement provider fallback based on actual data availability/error semantics.

Do this without creating duplicate provider calls unnecessarily.

---

# 27. AMAZON HISTORY

Keep ASIN-driven history when an ASIN is available.

Do not replace strong identifiers with fuzzy canonical names unnecessarily.

For Amazon:

ASIN
→ preferred historical identifier.

For platforms without a strong identifier:

Use the best available combination of:

- normalized product identity
- platform
- listing URL
- external ID

Avoid cross-listing contamination.

---

# 28. OWN DATABASE HISTORY

Audit the existing own-database historical provider.

Ensure that historical observations for:

Product A / Platform A / Listing A

do not accidentally become historical observations for:

Product A / Platform A / Listing B

unless that is intentionally part of the metric.

The system should preserve listing identity wherever practical.

---

# 29. MOVEMENT ANALYTICS

Audit 24H / 7D / 30D / 90D calculations.

Do not label a metric "7D change" if it is actually comparing against an arbitrary observation within ±2 days.

Define exact semantics.

For example:

7D change:

current reference price

vs.

price nearest to exactly 7 days ago

within an explicitly documented tolerance.

If there is insufficient historical data:

return:

NO_DATA

not:

STABLE

These are different states.

---

# 30. VOLATILITY

Audit the existing volatility implementation.

The current implementation is based on consecutive observations.

That is not automatically the same as daily volatility.

Do not call it "daily volatility" unless data is actually resampled by day.

Use terminology such as:

Observation-to-observation volatility

if that is what the implementation measures.

If implementing daily volatility, explicitly resample/aggregate observations by date first.

---

# 31. PRICE HISTORY GRAPH

Audit:

Price History

and

Average Price Over Time

graphs.

Ensure:

- invalid observations excluded
- corrupted values excluded from derived analytics
- multiple observations on the same day have defined behavior
- platform lines are consistent
- missing days do not create fake prices
- no interpolation is presented as actual observed data unless clearly labelled

For multiple observations on one day, define whether the graph uses:

- latest
- average
- median
- minimum

and apply it consistently.

---

# 32. CHEAPEST PLATFORM

"Where is it cheapest?" should use VERIFIED CURRENT prices only.

If multiple listings exist:

Find the cheapest verified listing.

Do not let an unverified search price determine the winner.

If no verified price exists:

show:

"No verified price available"

rather than guessing.

---

# 33. HISTORICALLY CHEAPEST

Rename ambiguous terminology if necessary.

For example:

"Historically Cheapest"

could misleadingly imply a single historical lowest point.

Prefer something like:

"Lowest Historical Average"

if the implementation calculates the platform with the lowest historical mean.

The UI terminology must match the actual calculation.

---

# 34. MOST CONSISTENT PLATFORM

The existing coefficient-of-variation concept can be retained if appropriate.

But make the label explicit:

"Lowest Price Variability (CV)"

rather than implying that it represents scraping reliability or temporal volatility.

Do not confuse:

price consistency

with

data-source reliability.

---

# 35. DATA PROVENANCE

The dashboard should make it clear where information came from.

Example:

Amazon
Discovery: Search
Current price: Verified by Amazon adapter
History: Keepa

Flipkart
Discovery: Search
Current price: Unverified
History: Own tracker

Croma
Discovery: Search
Current price: Unverified
History: None

Do not represent unverified search-engine data as verified tracker data.

---

# 36. NO FAKE DATA

In production mode:

Never generate fake current prices.

Never generate fake historical prices.

Never substitute:

0

for missing price.

Never substitute:

current price

for missing historical price.

Never mark:

FAILED

as:

STABLE.

Demo mode can continue using synthetic data if the existing application intentionally supports it, but demo data must remain clearly isolated/labeled.

---

# 37. FRONTEND BEHAVIOR

The frontend should show a comprehensive market-discovery table.

Example:

| Platform | Product | Price | Status | Action |
|----------|---------|-------|--------|--------|
| Amazon | Galaxy S26 Ultra | ₹1,39,999 | Verified | View |
| Flipkart | Galaxy S26 Ultra | ₹1,30,999 | Verified | View |
| Croma | Galaxy S26 Ultra | — | Unverified | View |
| Reliance Digital | Galaxy S26 Ultra | — | Unverified | View |
| Samsung | Galaxy S26 Ultra | — | Unverified | View |

The user should be able to inspect every discovered market option.

Do NOT hide rows because their scraper failed.

---

# 38. DASHBOARD SUMMARY RULE

Dashboard summary cards should only use valid verified data.

For example:

Current Lowest:
minimum VERIFIED price

Current Average:
mean VERIFIED prices

Current Highest:
maximum VERIFIED price

If only 2 of 8 discovered results are verified:

the dashboard may say:

2 verified prices across 8 discovered listings

This is preferable to pretending all 8 have valid prices.

---

# 39. VERIFIED COVERAGE

Add a useful concept:

Verified Coverage

Example:

5 / 9 listings verified

or:

56% verified

This gives the user context about how complete current price data is.

Do not use this as a quality score/ranking.

It is simply factual coverage information.

---

# 40. SEARCH RESULT COUNT

Ensure the Search object/results metadata accurately distinguishes:

discovered results

from:

verified results

For example:

discovered_count = 9
verified_count = 5

Do not report:

results_count = 5

if 9 products were discovered.

---

# 41. TESTING REQUIREMENTS

Add comprehensive tests.

At minimum test:

## Discovery

1. Relevant result + scraper success → retained.
2. Relevant result + scraper failure → retained.
3. Relevant result + timeout → retained.
4. Relevant result + HTTP 403 → retained.
5. Relevant result + no price extracted → retained.
6. Irrelevant result + scraper success → removed.
7. Duplicate exact URL → deduplicated.
8. Different URLs on same domain → both retained.

---

## Price handling

9. Verified price → current analytics eligible.
10. Search-only price → not historical eligible.
11. Failed scrape with provisional price → not historical eligible.
12. Missing price → no fake zero.
13. No verified prices → no fake current average.

---

## Historical data

14. Verified observation saved.
15. Failed/unverified observation not saved.
16. Invalid zero-price observation rejected.
17. Invalid negative price rejected.
18. Raw suspicious observation preserved/flagged appropriately.
19. Provider returns no data → fallback provider attempted.
20. Provider succeeds → fallback not unnecessarily called.

---

## Analytics

21. Current average uses verified current prices.
22. Current lowest uses verified current prices.
23. Current highest uses verified current prices.
24. Current-vs-historical average uses average vs average.
25. No historical data → NO_DATA.
26. 7D with insufficient data → NO_DATA.
27. 7D does not report STABLE simply because no observation exists.
28. Historical platform average follows explicitly defined weighting.
29. Multiple observations on same date follow defined aggregation.
30. Outlier handling does not destroy raw observation.

---

## Frontend

31. Failed scrape result remains visible.
32. Failed scrape result has clickable link.
33. Price unavailable displays correctly.
34. MRP is not shown.
35. Discount is not shown.
36. Shipping is not shown.
37. Seller is not shown.
38. Verified/unverified status is clearly visible.
39. Dashboard summary ignores unverified prices.
40. Multiple listings from same platform remain visible.

---

# 42. API CONTRACT

Audit API schemas.

Make sure the API clearly represents:

- discovered result
- URL
- platform
- title/product name
- provisional/discovered price if available
- verified price if available
- verification status
- link

Do not force clients to infer whether a price is verified.

Prefer explicit fields/statuses.

Avoid unnecessary fields.

---

# 43. DATABASE SAFETY

Do not perform destructive migrations casually.

Before changing models:

1. Inspect existing Alembic migrations.
2. Inspect current schema.
3. Determine whether a migration is actually required.
4. Preserve existing historical data.
5. Do not wipe the database.
6. Do not reset tables as a shortcut.

If fields are no longer user-facing but are still needed internally, they may remain in the database.

The goal is a clean product/API model, not needless destructive schema cleanup.

---

# 44. PERFORMANCE

Do not turn every discovered result into an expensive scrape if unnecessary.

The intended architecture should remain:

1. Search once.
2. Filter/classify candidates.
3. Preserve discovered candidates.
4. Attempt verification with controlled concurrency.
5. Return results quickly where possible.
6. Enrich asynchronously where the current architecture already supports it.

Maintain concurrency limits and timeouts.

Do not introduce uncontrolled parallel scraping.

---

# 45. LLM CALL BUDGET

Audit the current Gemini usage.

The system currently has query parsing and batch classification capabilities.

Do not accidentally create:

one LLM call per search result.

Classification should remain batched.

Do not introduce another LLM stage unless necessary.

The LLM should solve semantic matching, not perform deterministic price processing.

---

# 46. SEARCH RESPONSE UX

The initial search response should not require all scrapers to finish before showing discovered market options if the current architecture supports asynchronous enrichment.

Ideal flow:

T = 0

Search provider returns candidates.

Frontend receives:

Amazon → verifying
Flipkart → verifying
Croma → verifying
Samsung → verifying

Then asynchronously:

Amazon → ₹1,39,999 verified
Flipkart → ₹1,30,999 verified
Croma → price unavailable
Samsung → price unavailable

The user should not lose discovered options during this process.

---

# 47. ERROR HANDLING

Scraper failures should be isolated per listing.

One adapter failure must not fail the entire search.

Bad:

Flipkart timeout
→ entire search fails

Correct:

Flipkart timeout
→ Flipkart result = UNVERIFIED

while the rest continue.

Similarly:

Amazon adapter exception

must not remove:

Amazon URL

from discovery results.

---

# 48. LOGGING

Log enough information to debug failures.

For example:

[DISCOVERY]
Found result: Flipkart URL

[VERIFICATION]
Attempting Flipkart URL

[VERIFICATION]
Failed: timeout

[RESULT]
Retaining discovered URL as UNVERIFIED

Do not expose sensitive credentials.

Avoid excessive logging of entire HTML pages.

---

# 49. CLEAN ARCHITECTURE

Maintain separation between:

SearchProvider
    ↓
Candidate Discovery
    ↓
Relevance Classification
    ↓
Candidate Persistence
    ↓
Price Verification
    ↓
Historical Persistence
    ↓
Analytics

Do not merge these concerns.

In particular:

Price verification must NOT decide whether discovery candidates exist.

---

# 50. OBSERVATIONS FROM THE EXISTING PROJECT THAT MUST NOT BE LOST

Preserve and correct the following existing useful behavior:

### A. Search-engine discovery

The application uses search results to discover real market options.

Do not replace this with a small fixed list of websites.

---

### B. Provisional price extraction

Search result metadata can provide useful price information.

Keep it as discovery/provisional information.

Do not treat it as verified historical data.

---

### C. Adapter-based verification

Keep the adapter architecture.

Amazon/Flipkart/Generic/etc. can independently verify discovered URLs.

---

### D. Historical providers

Keep the provider architecture:

Keepa
Own Database
Demo

but make fallback/data-quality behavior correct.

---

### E. Asynchronous enrichment

Preserve the fast initial search + background enrichment architecture if it is working.

---

# 51. DO NOT DO THESE THINGS

Do NOT:

- remove a result because scraping failed
- remove a URL because price extraction failed
- use 0 for missing prices
- save unverified prices as verified historical observations
- calculate current averages from unverified prices
- calculate historical analytics from known-invalid observations
- deduplicate all results by domain
- keep only one Amazon listing
- keep only one Flipkart listing
- hide failed listings
- fabricate shipping
- show MRP
- show discount
- show seller
- show shipping
- create fake historical data in production
- add unrelated features
- rewrite the application unnecessarily
- replace the search architecture with a hardcoded marketplace list
- increase LLM calls unnecessarily
- make the LLM responsible for deterministic logic

---

# 52. IMPLEMENTATION ORDER

Follow this order.

## Phase 1 — Inspect

Read:

backend search pipeline
backend schemas
backend models
search provider
LLM service
adapters
history providers
analytics
API routes
frontend dashboard
tests
Alembic migrations

Run current tests.

---

## Phase 2 — Discovery correctness

Fix:

- result retention
- scraper failure handling
- exact URL deduplication
- removal of domain-level deduplication
- persistent links
- independent verification status

---

## Phase 3 — Price model

Fix:

- discovered/provisional price
- verified price
- verification status
- missing price handling
- no fake effective price
- remove unnecessary core fields

---

## Phase 4 — Historical integrity

Fix:

- only verified observations enter own history
- provenance
- confidence
- invalid observation filtering
- listing identity
- provider fallback

---

## Phase 5 — Analytics

Fix:

- verified current statistics
- current vs historical average
- historical weighting semantics
- outlier handling
- movement semantics
- volatility terminology
- price-position calculation
- same-day aggregation

---

## Phase 6 — Frontend

Fix:

- minimal table
- platform
- product/listing
- price
- status
- link
- verified coverage
- no MRP
- no discount
- no shipping
- no seller
- failed result visibility

---

## Phase 7 — Tests

Add the comprehensive test matrix above.

Run backend tests.

Run frontend tests/build if available.

---

# 53. FINAL ACCEPTANCE CRITERIA

The implementation is NOT complete unless all of the following are true.

### Discovery

[ ] Search discovers multiple market options.

[ ] Multiple URLs from the same platform can survive.

[ ] Exact duplicate URLs are removed.

[ ] Scraping failure does NOT remove discovered URLs.

[ ] Search results remain clickable.

---

### Price verification

[ ] Verified prices are clearly identified.

[ ] Failed prices are clearly identified.

[ ] Missing prices are not converted to zero.

[ ] Search-engine prices are distinguishable from verified prices.

---

### Historical integrity

[ ] Failed/unverified prices NEVER enter own historical observations as verified data.

[ ] Historical observations contain provenance.

[ ] Invalid observations are not used for analytics.

[ ] Raw suspicious observations are not blindly destroyed.

---

### Analytics

[ ] Current analytics use verified prices only.

[ ] Historical analytics use quality-controlled observations.

[ ] Current-vs-historical-average calculation is mathematically correct.

[ ] Missing historical periods return NO_DATA rather than STABLE.

[ ] Historical weighting semantics are documented.

[ ] Volatility terminology matches implementation.

---

### UI

[ ] Platform is shown.

[ ] Product/listing is shown.

[ ] Price is shown when available.

[ ] Verification status is shown.

[ ] Product link is always available.

[ ] MRP is removed.

[ ] Discount is removed.

[ ] Shipping is removed.

[ ] Seller is removed.

[ ] Failed scraping does not hide the listing.

---

# 54. REQUIRED FINAL REPORT

After implementation, do NOT simply say "done".

Provide a concise engineering report containing:

## 1. Files changed

List every modified file.

## 2. Discovery changes

Explain exactly how scraper failure behavior changed.

## 3. Price changes

Explain discovered vs verified price handling.

## 4. Historical changes

Explain what is now allowed into PriceObservation.

## 5. Analytics changes

Explain every corrected metric.

## 6. Frontend changes

Explain the new minimal table.

## 7. Tests

Report:

- tests before
- tests after
- tests passed
- tests failed
- build status

## 8. Remaining issues

Explicitly list anything that could not be completed.

Do NOT hide failures.

---

# 55. FINAL PRINCIPLE

The product should behave like a:

## MARKET DISCOVERY + PRICE VERIFICATION + PRICE HISTORY SYSTEM

NOT:

## SCRAPER SUCCESS = RESULT EXISTS

The correct behavior is:

SEARCH FINDS IT
    ↓
KEEP THE LINK
    ↓
TRY TO VERIFY
    ↓
SUCCESS → SHOW VERIFIED PRICE
FAILURE → SHOW LINK + PRICE UNAVAILABLE/UNVERIFIED
    ↓
ONLY TRUST VERIFIED/QUALITY-CONTROLLED DATA FOR ANALYTICS AND HISTORY

This distinction is fundamental to the product.

Implement the changes carefully against the CURRENT repository.

Do not rebuild what already works.

Do not remove market discovery capability.

Do not allow scraper failures to destroy discovery results.

Do not contaminate historical analytics with unverified prices.

Start by inspecting the repository and running the existing test suite.