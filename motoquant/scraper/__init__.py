"""
MotoQuant Pro — Bike Data Scraper Pipeline
==========================================
Fetches, validates, and imports motorcycle specifications from public sources
into the MotoQuant database.

Pipeline stages:
    1. Fetch  — HTTP GET with retry + rate-limit backoff
    2. Parse  — extract BikeSpec from HTML/JSON with provenance metadata
    3. Validate — sanity-check specs against physical bounds + cross-ref
    4. Score   — compute confidence score per field
    5. Import  — upsert into bike_models / bike_configs with provenance records

Entry points:
    BikeSpec        dataclass for scraped raw data
    scrape_bikez    scrape a single Bikez.com bike page
    crawl_bikez     crawl a model listing, yielding BikeSpec objects
    import_spec     push a BikeSpec into MotoQuantDB
    run_pipeline    end-to-end: crawl → validate → import → report
"""

from .bikez import crawl_bikez, scrape_bikez
from .importer import import_batch, import_spec
from .spec import BikeSpec, ValidationResult
from .validator import score_spec, validate_spec

__all__ = [
    "BikeSpec",
    "ValidationResult",
    "scrape_bikez",
    "crawl_bikez",
    "validate_spec",
    "score_spec",
    "import_spec",
    "import_batch",
]
