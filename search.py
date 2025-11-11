#!/usr/bin/env python3
"""
Søk etter "historiske spel" i Nasjonalbibliotekets avisarkiv 2015-2025
MED DUPLIKATKONTROLL - teller hver unike artikkel kun én gang

VIKTIG: Hver artikkel har en unik URN (Uniform Resource Name).
Dette scriptet fjerner duplikater basert på URN før telling.
"""

from dhlab import Corpus
import pandas as pd
import sys
import argparse

# KONFIGURASJON (standard verdier, kan overstyres via kommandolinje)
SEARCH_TYPE = "exact_phrase"  # Alternativer: "fulltext", "freetext", "exact_phrase"
SEARCH_TERM = "historiske spel"
FROM_YEAR = 2015
TO_YEAR = 2025
MAX_RESULTS = 2000

# VIKTIG:
# - "fulltext" finner artikler med 'historiske' ELLER 'spel' (gir mange treff)
# - "exact_phrase" finner kun artikler med den eksakte frasen 'historiske spel' (anbefalt)


def create_pivot_table(search_type="freetext", search_term=None, from_year=None, to_year=None, max_results=None):
    """
    Søk etter articles og lag pivottabell med duplikatkontroll
    """
    # Use defaults if not provided
    if search_term is None:
        search_term = SEARCH_TERM
    if from_year is None:
        from_year = FROM_YEAR
    if to_year is None:
        to_year = TO_YEAR
    if max_results is None:
        max_results = MAX_RESULTS

    print("=" * 80)
    print("SØKER I NASJONALBIBLIOTEKETS AVISARKIV (MED DUPLIKATKONTROLL)")
    print("=" * 80)
    print(f"\nSøkeord: '{search_term}'")
    print(f"Søketype: {search_type}")
    print(f"Periode: {from_year}-{to_year}")
    print(f"\nHenter data fra NB's API...")
    print("(Dette kan ta 30-60 sekunder)\n")

    try:
        # NOTE: dhlab's to_year seems to be exclusive, so we add 1 to include the full year
        # For example, to get articles from 2025, we need to set to_year=2026
        api_to_year = to_year + 1

        # Create corpus based on search type
        if search_type == "fulltext":
            print("ℹ️  FULLTEXT: Søker i ALL OCR'et tekst")
            corpus = Corpus(
                doctype='digavis',
                fulltext=search_term,
                from_year=from_year,
                to_year=api_to_year,
                limit=max_results
            )
        elif search_type == "freetext":
            print("ℹ️  FREETEXT: Søker i indeksert fritekst")
            corpus = Corpus(
                doctype='digavis',
                freetext=search_term,
                from_year=from_year,
                to_year=api_to_year,
                limit=max_results
            )
        elif search_type == "exact_phrase":
            print("ℹ️  EXACT PHRASE: Søker etter eksakt frase")
            corpus = Corpus(
                doctype='digavis',
                fulltext=f'"{search_term}"',
                from_year=from_year,
                to_year=api_to_year,
                limit=max_results
            )
        else:
            print(f"❌ Ukjent søketype: {search_type}")
            sys.exit(1)
        
        # Get corpus data as DataFrame
        df = corpus.corpus
        
        if df.empty:
            print("❌ Ingen resultater funnet.")
            return None
        
        print(f"✅ Hentet {len(df)} objekter fra API\n")
        
        # CHECK FOR DUPLICATES
        print("🔍 Sjekker for duplikater...")
        print(f"   Før duplikatkontroll: {len(df)} rader")
        
        # Check if URN column exists
        if 'urn' not in df.columns:
            print("   ⚠️  Ingen URN-kolonne funnet. Tilgjengelige kolonner:")
            print(f"   {', '.join(df.columns)}")
            print("\n   Bruker alle kolonner for å identifisere unike artikler...")
            # Use all columns to identify duplicates if no URN
            df_unique = df.drop_duplicates()
        else:
            # Remove duplicates based on URN
            initial_count = len(df)
            df_unique = df.drop_duplicates(subset=['urn'])
            removed = initial_count - len(df_unique)
            
            print(f"   Etter duplikatkontroll: {len(df_unique)} unike artikler")
            if removed > 0:
                print(f"   ⚠️  Fjernet {removed} duplikater ({removed/initial_count*100:.1f}%)")
            else:
                print(f"   ✓ Ingen duplikater funnet")
        
        print()
        
        # Show sample of data for debugging
        print("📋 Eksempel på data (første 5 rader):")
        print("-" * 80)
        display_cols = ['title', 'year', 'timestamp'] if 'timestamp' in df_unique.columns else ['title', 'year']
        if 'urn' in df_unique.columns:
            display_cols.append('urn')
        print(df_unique[display_cols].head().to_string(index=False))
        print()
        
        # Create pivot table: newspapers (rows) x years (columns)
        pivot = pd.crosstab(
            index=df_unique['title'],
            columns=df_unique['year'],
            margins=True,
            margins_name='TOTAL'
        )
        
        # Sort by total (descending)
        pivot = pivot.sort_values('TOTAL', ascending=False)
        
        # Display table
        print("=" * 80)
        print(f"UNIKE ARTIKLER OM '{search_term}' PER AVIS OG ÅR")
        print(f"Søketype: {search_type.upper()}")
        print("=" * 80)
        print()
        print(pivot.to_string())
        print()

        # Create filename-safe search term
        safe_search_term = search_term.replace(' ', '_').replace('"', '').replace("'", '')

        # Save to CSV
        output_file = f'{safe_search_term}_UNIKE_{search_type}_{from_year}_{to_year}.csv'
        pivot.to_csv(output_file, encoding='utf-8-sig')
        print(f"💾 Tabell lagret til: {output_file}")

        # Save detailed list with URNs
        if 'urn' in df_unique.columns:
            detail_cols = ['year', 'title', 'urn']
            if 'timestamp' in df_unique.columns:
                detail_cols = ['timestamp', 'title', 'urn', 'year']
            detail_file = f'{safe_search_term}_DETALJER_{search_type}_{from_year}_{to_year}.csv'
            df_unique[detail_cols].sort_values('year').to_csv(detail_file, index=False, encoding='utf-8-sig')
            print(f"📄 Detaljert liste lagret til: {detail_file}")
        
        # Additional statistics
        print("\n" + "=" * 80)
        print("STATISTIKK")
        print("=" * 80)
        print(f"\nTotal UNIKE artikler: {len(df_unique)}")
        print(f"Antall aviser: {df_unique['title'].nunique()}")
        print(f"Periode: {df_unique['year'].min()} - {df_unique['year'].max()}")
        
        print(f"\nTopp 10 aviser (totalt):")
        top_papers = pivot['TOTAL'].head(11)
        for i, (avis, count) in enumerate(top_papers.items(), 1):
            if avis != 'TOTAL':
                print(f"  {i:2d}. {avis:40s} {int(count):4d} artikler")
        
        print(f"\nArtikler per år:")
        yearly = df_unique.groupby('year').size().sort_index()
        total_articles = yearly.sum()
        for year, count in yearly.items():
            bar = '█' * min(count // 2, 50)
            pct = count / total_articles * 100
            print(f"  {year}: {count:4d} ({pct:5.1f}%) {bar}")
        
        print("\n" + "=" * 80)
        print("SØKETYPER:")
        print("=" * 80)
        print("""
freetext     = Søker i indeksert fritekst (anbefalt for å matche manuelt søk)
fulltext     = Søker i ALL OCR'et tekst (mest omfattende)
exact_phrase = Søker etter eksakt frase (strengest)
        """)
        
        return pivot, df_unique
        
    except Exception as e:
        print(f"\n❌ FEIL: {e}")
        print("\nMulige årsaker:")
        print("1. Ingen tilgang til api.nb.no")
        print("2. dhlab ikke installert (kjør: pip install dhlab)")
        print("3. Nettverksproblemer")
        sys.exit(1)


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Søk i Nasjonalbibliotekets avisarkiv',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--search-term', type=str, default=SEARCH_TERM,
                        help=f'Søkeord (standard: "{SEARCH_TERM}")')
    parser.add_argument('--from-year', type=int, default=FROM_YEAR,
                        help=f'Fra år (standard: {FROM_YEAR})')
    parser.add_argument('--to-year', type=int, default=TO_YEAR,
                        help=f'Til år (standard: {TO_YEAR})')
    parser.add_argument('--search-type', type=str, default=SEARCH_TYPE,
                        choices=['exact_phrase', 'fulltext', 'freetext'],
                        help=f'Søketype (standard: {SEARCH_TYPE})')
    parser.add_argument('--max-results', type=int, default=MAX_RESULTS,
                        help=f'Max antall resultater (standard: {MAX_RESULTS})')

    args = parser.parse_args()

    print("\n")
    print("💡 VIKTIG: Dette scriptet fjerner duplikater før telling")
    print(f"   Søketype: '{args.search_type}'")
    print(f"   Søkeord: '{args.search_term}'")
    print(f"   Periode: {args.from_year}-{args.to_year}")
    print()

    result = create_pivot_table(
        search_type=args.search_type,
        search_term=args.search_term,
        from_year=args.from_year,
        to_year=args.to_year,
        max_results=args.max_results
    )

    if result is None:
        print("\n" + "=" * 80)
        print("AVBRUTT")
        print("=" * 80)
        print("\n❌ Søket returnerte ingen resultater eller feilet.")
        print("   Se feilmeldinger ovenfor for detaljer.")
        sys.exit(1)

    pivot, df_unique = result

    print("\n" + "=" * 80)
    print("FERDIG!")
    print("=" * 80)
    print(f"\n✓ Hver artikkel er telt KUN ÉN GANG (basert på unik URN)")
    print()


if __name__ == '__main__':
    main()
