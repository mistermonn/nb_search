#!/usr/bin/env python3
"""
Test-script for å diagnostisere søkeproblemer med dhlab
Prøver flere forskjellige søkemetoder for å finne ut hva som fungerer
"""

from dhlab import Corpus
import pandas as pd

SEARCH_TERM = "historiske spel"
FROM_YEAR = 2015
TO_YEAR = 2025
MAX_RESULTS = 100  # Lavere limit for testing

def test_method(name, **kwargs):
    """Test en søkemetode og vis resultatene"""
    print("\n" + "=" * 80)
    print(f"TEST: {name}")
    print("=" * 80)
    print(f"Parametere: {kwargs}")

    try:
        corpus = Corpus(**kwargs)
        df = corpus.corpus

        print(f"✅ Corpus opprettet")
        print(f"   - Type: {type(df)}")
        print(f"   - Shape: {df.shape if hasattr(df, 'shape') else 'N/A'}")
        print(f"   - Kolonner: {df.columns.tolist() if hasattr(df, 'columns') else 'N/A'}")
        print(f"   - Antall rader: {len(df) if hasattr(df, '__len__') else 'N/A'}")

        if hasattr(df, 'empty') and not df.empty:
            print(f"\n🎉 SUKSESS! Fant {len(df)} resultater")
            print("\nFørste rad:")
            print(df.head(1))
            return True
        else:
            print(f"⚠️  DataFrame er tom")
            return False

    except Exception as e:
        print(f"❌ FEIL: {e}")
        return False

def main():
    print("🧪 TESTING DHLAB SØKEMETODER")
    print(f"Søker etter: '{SEARCH_TERM}'")
    print(f"Periode: {FROM_YEAR}-{TO_YEAR}")
    print()

    results = {}

    # Test 1: freetext
    results['freetext'] = test_method(
        "FREETEXT (standard)",
        doctype='digavis',
        freetext=SEARCH_TERM,
        from_year=FROM_YEAR,
        to_year=TO_YEAR,
        limit=MAX_RESULTS
    )

    # Test 2: fulltext
    results['fulltext'] = test_method(
        "FULLTEXT (OCR-tekst)",
        doctype='digavis',
        fulltext=SEARCH_TERM,
        from_year=FROM_YEAR,
        to_year=TO_YEAR,
        limit=MAX_RESULTS
    )

    # Test 3: exact phrase
    results['exact_phrase'] = test_method(
        "EXACT PHRASE (med anførselstegn)",
        doctype='digavis',
        fulltext=f'"{SEARCH_TERM}"',
        from_year=FROM_YEAR,
        to_year=TO_YEAR,
        limit=MAX_RESULTS
    )

    # Test 4: Enkelt ord
    results['single_word'] = test_method(
        "ENKELT ORD (kun 'historiske')",
        doctype='digavis',
        freetext="historiske",
        from_year=FROM_YEAR,
        to_year=TO_YEAR,
        limit=MAX_RESULTS
    )

    # Test 5: AND-operator
    results['and_operator'] = test_method(
        "AND-OPERATOR (historiske AND spel)",
        doctype='digavis',
        freetext="historiske AND spel",
        from_year=FROM_YEAR,
        to_year=TO_YEAR,
        limit=MAX_RESULTS
    )

    # Test 6: Uten limit
    results['no_limit'] = test_method(
        "UTEN LIMIT",
        doctype='digavis',
        freetext=SEARCH_TERM,
        from_year=FROM_YEAR,
        to_year=TO_YEAR
    )

    # Test 7: Kun ett år
    results['single_year'] = test_method(
        "ENKELT ÅR (2023)",
        doctype='digavis',
        freetext=SEARCH_TERM,
        from_year=2023,
        to_year=2023,
        limit=MAX_RESULTS
    )

    # Oppsummering
    print("\n" + "=" * 80)
    print("OPPSUMMERING")
    print("=" * 80)

    for method, success in results.items():
        status = "✅ FUNGERER" if success else "❌ INGEN RESULTATER"
        print(f"{method:20s}: {status}")

    print("\n" + "=" * 80)

    if not any(results.values()):
        print("⚠️  INGEN METODER GA RESULTATER")
        print("\nMulige årsaker:")
        print("1. Du mangler forskertilgang til NB's API")
        print("2. Nettverksproblemer eller API er nede")
        print("3. dhlab-biblioteket må oppdateres: pip install --upgrade dhlab")
        print("4. Søkeordet finnes ikke i denne perioden")
        print("\nPrøv å:")
        print("- Gå til https://www.nb.no og søk manuelt")
        print("- Sjekk om du har BankID/MinID-innlogging på nb.no")
        print("- Kontakt NB support: avis@nb.no")
    else:
        print("✅ Minst én metode fungerte! Bruk den metoden i search.py")

if __name__ == '__main__':
    main()
