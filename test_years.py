#!/usr/bin/env python3
"""
Test for å se hvilke år som faktisk returneres fra API-et
"""

from dhlab import Corpus
import pandas as pd

SEARCH_TERM = "historiske spel"
FROM_YEAR = 2015
TO_YEAR = 2025

print("=" * 80)
print("TEST: Hvilke år returnerer API-et?")
print("=" * 80)
print()

# Test med to_year = 2025
print(f"TEST 1: to_year=2025 (som du oppga)")
corpus1 = Corpus(
    doctype='digavis',
    fulltext=f'"{SEARCH_TERM}"',
    from_year=FROM_YEAR,
    to_year=TO_YEAR,
    limit=500
)
df1 = corpus1.corpus
if not df1.empty:
    years1 = sorted(df1['year'].unique())
    print(f"   Antall artikler: {len(df1)}")
    print(f"   År i resultatet: {years1}")
    print(f"   Første år: {min(years1)}, Siste år: {max(years1)}")
else:
    print("   Ingen resultater")

print()

# Test med to_year = 2026 (to_year + 1)
print(f"TEST 2: to_year=2026 (to_year + 1)")
corpus2 = Corpus(
    doctype='digavis',
    fulltext=f'"{SEARCH_TERM}"',
    from_year=FROM_YEAR,
    to_year=TO_YEAR + 1,
    limit=500
)
df2 = corpus2.corpus
if not df2.empty:
    years2 = sorted(df2['year'].unique())
    print(f"   Antall artikler: {len(df2)}")
    print(f"   År i resultatet: {years2}")
    print(f"   Første år: {min(years2)}, Siste år: {max(years2)}")
else:
    print("   Ingen resultater")

print()

# Test med to_year = 2027 (to_year + 2)
print(f"TEST 3: to_year=2027 (to_year + 2)")
corpus3 = Corpus(
    doctype='digavis',
    fulltext=f'"{SEARCH_TERM}"',
    from_year=FROM_YEAR,
    to_year=TO_YEAR + 2,
    limit=500
)
df3 = corpus3.corpus
if not df3.empty:
    years3 = sorted(df3['year'].unique())
    print(f"   Antall artikler: {len(df3)}")
    print(f"   År i resultatet: {years3}")
    print(f"   Første år: {min(years3)}, Siste år: {max(years3)}")
else:
    print("   Ingen resultater")

print()
print("=" * 80)
print("KONKLUSJON:")
print("=" * 80)

if not df1.empty and max(df1['year'].unique()) < TO_YEAR:
    print(f"⚠️  TEST 1 (to_year={TO_YEAR}) inkluderer IKKE {TO_YEAR}")
if not df2.empty and max(df2['year'].unique()) >= TO_YEAR:
    print(f"✅ TEST 2 (to_year={TO_YEAR + 1}) inkluderer {TO_YEAR}!")
else:
    print(f"⚠️  TEST 2 (to_year={TO_YEAR + 1}) inkluderer IKKE {TO_YEAR}")

if not df3.empty:
    print(f"   TEST 3 (to_year={TO_YEAR + 2}) gir år: {sorted(df3['year'].unique())}")

print()
print("💡 Det kan også være at NB ennå ikke har digitalisert aviser fra 2025")
print("   eller at de ikke er tilgjengelige via API-et ennå.")
