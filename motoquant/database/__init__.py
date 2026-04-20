"""
MotoQuant Pro — Database Layer
============================
SQLite-backed storage for motorcycles, tires, venues, weather, and parts.

Phase 2 of MotoQuant: persistent, queryable, provenance-tracked data.

Usage:
    from motoquant.database import MotoQuantDB

    db = MotoQuantDB("motoquant.db")
    db.initialize()

    # Store a bike from existing config
    from motoquant.defaults import gsxr1000_k5
    bike_id = db.bikes.upsert_from_config(gsxr1000_k5())

    # Query
    results = db.bikes.search(displacement_min=900, category="sport")
    config = db.bikes.to_config(bike_id)  # → BikeConfig ready for simulation
"""

__version__ = "0.1.0"

from .connection import MotoQuantDB
from .schema import SCHEMA_VERSION

__all__ = ["MotoQuantDB", "SCHEMA_VERSION"]
