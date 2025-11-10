#!/usr/bin/env python3
"""
Sammenlign fulltext vs exact_phrase søk for å se forskjellen
"""

from dhlab import Corpus
import pandas as pd

SEARCH_TERM = "historiske spel"
FROM_YEAR = 2015
TO_YEAR = 2025
MAX_RESULTS = 2000

print("=" * 80)
print("SAMMENLIGNING AV SØKEMETODER")
print("=" * 80)
print(f"Søkeord: '{SEARCH_TERM}'")
print(f"Periode: {FROM_YEAR}-{TO_YEAR}")
print(f"Max resultater: {MAX_RESULTS}")
print()

# Test 1: fulltext (uten anførselstegn)
print("🔍 TEST 1: FULLTEXT (uten anførselstegn)")
print("   Dette kan finne artikler med 'historiske' ELLER 'spel'")
corpus1 = Corpus(
    doctype='digavis',
    fulltext=SEARCH_TERM,
    from_year=FROM_YEAR,
    to_year=TO_YEAR,
    limit=MAX_RESULTS
)
df1 = corpus1.corpus
print(f"   ✅ Resultat: {len(df1)} artikler")

# Test 2: exact phrase (med anførselstegn)
print("\n🔍 TEST 2: EXACT PHRASE (med anførselstegn)")
print("   Dette finner kun artikler med eksakt 'historiske spel'")
corpus2 = Corpus(
    doctype='digavis',
    fulltext=f'"{SEARCH_TERM}"',
    from_year=FROM_YEAR,
    to_year=TO_YEAR,
    limit=MAX_RESULTS
)
df2 = corpus2.corpus
print(f"   ✅ Resultat: {len(df2)} artikler")

# Sammenligning
print("\n" + "=" * 80)
print("SAMMENLIGNING")
print("=" * 80)
print(f"Fulltext (uten anførselstegn):  {len(df1):4d} artikler")
print(f"Exact phrase (med anførselstegn): {len(df2):4d} artikler")
print(f"Forskjell:                        {len(df1) - len(df2):4d} artikler")
print()

if len(df1) > len(df2):
    print("⚠️  KONKLUSJON:")
    print(f"   Fulltext finner {len(df1) - len(df2)} FLERE artikler enn exact phrase!")
    print("   Dette betyr at fulltext trolig finner artikler med")
    print("   'historiske' ELLER 'spel', ikke nødvendigvis sammen.")
    print()
    print("   💡 ANBEFALING: Bruk 'exact_phrase' for å finne kun artikler")
    print("      som inneholder den eksakte frasen 'historiske spel'")
elif len(df1) == len(df2):
    print("✅ KONKLUSJON:")
    print("   Begge metodene gir samme antall resultater.")
    print("   Du kan bruke begge.")
else:
    print("❓ KONKLUSJON:")
    print("   Exact phrase finner flere enn fulltext (uventet)")

# Fjern duplikater basert på URN
if 'urn' in df1.columns:
    df1_unique = df1.drop_duplicates(subset=['urn'])
    print(f"\nEtter duplikatkontroll (fulltext): {len(df1_unique)} unike artikler")

if 'urn' in df2.columns:
    df2_unique = df2.drop_duplicates(subset=['urn'])
    print(f"Etter duplikatkontroll (exact phrase): {len(df2_unique)} unike artikler")

print("\n" + "=" * 80)
