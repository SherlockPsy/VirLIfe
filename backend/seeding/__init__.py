"""
Seeding module for baseline world population.

This module implements deterministic mapping from raw data files to database schema,
and provides the seed_baseline_world() entry point for populating the baseline world.
"""

from .seed_baseline_world import seed_baseline_world

__all__ = ["seed_baseline_world"]

