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

# KONFIGURASJON
SEARCH_TYPE = "freetext"  # Alternativer: "fulltext", "freetext", "exact_phrase"
SEARCH_TERM = "historiske spel"
FROM_YEAR = 2015
TO_YEAR = 2025
MAX_RESULTS = 2000


def create_pivot_table(search_type="freetext"):
    """
    Søk etter 'historiske spel' og lag pivottabell med duplikatkontroll
    """
    print("=" * 80)
    print("SØKER I NASJONALBIBLIOTEKETS AVISARKIV (MED DUPLIKATKONTROLL)")
    print("=" * 80)
    print(f"\nSøkeord: '{SEARCH_TERM}'")
    print(f"Søketype: {search_type}")
    print(f"Periode: {FROM_YEAR}-{TO_YEAR}")
    print(f"\nHenter data fra NB's API...")
    print("(Dette kan ta 30-60 sekunder)\n")
    
    try:
        # Create corpus based on search type
        if search_type == "fulltext":
            print("ℹ️  FULLTEXT: Søker i ALL OCR'et tekst")
            corpus = Corpus(
                doctype='digavis',
                fulltext=SEARCH_TERM,
                from_year=FROM_YEAR,
                to_year=TO_YEAR,
                limit=MAX_RESULTS
            )
        elif search_type == "freetext":
            print("ℹ️  FREETEXT: Søker i indeksert fritekst")
            corpus = Corpus(
                doctype='digavis',
                freetext=SEARCH_TERM,
                from_year=FROM_YEAR,
                to_year=TO_YEAR,
                limit=MAX_RESULTS
            )
        elif search_type == "exact_phrase":
            print("ℹ️  EXACT PHRASE: Søker etter eksakt frase")
            corpus = Corpus(
                doctype='digavis',
                fulltext=f'"{SEARCH_TERM}"',
                from_year=FROM_YEAR,
                to_year=TO_YEAR,
                limit=MAX_RESULTS
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
        print(f"UNIKE ARTIKLER OM '{SEARCH_TERM}' PER AVIS OG ÅR")
        print(f"Søketype: {search_type.upper()}")
        print("=" * 80)
        print()
        print(pivot.to_string())
        print()
        
        # Save to CSV
        output_file = f'historiske_spel_UNIKE_{search_type}_{FROM_YEAR}_{TO_YEAR}.csv'
        pivot.to_csv(output_file, encoding='utf-8-sig')
        print(f"💾 Tabell lagret til: {output_file}")
        
        # Save detailed list with URNs
        if 'urn' in df_unique.columns:
            detail_cols = ['year', 'title', 'urn']
            if 'timestamp' in df_unique.columns:
                detail_cols = ['timestamp', 'title', 'urn', 'year']
            detail_file = f'historiske_spel_DETALJER_{search_type}_{FROM_YEAR}_{TO_YEAR}.csv'
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
    print("\n")
    print("💡 VIKTIG: Dette scriptet fjerner duplikater før telling")
    print(f"   Søketype: '{SEARCH_TYPE}' (endre i linje 15 om nødvendig)")
    print()
    
    pivot, df_unique = create_pivot_table(search_type=SEARCH_TYPE)
    
    print("\n" + "=" * 80)
    print("FERDIG!")
    print("=" * 80)
    print(f"\n✓ Hver artikkel er telt KUN ÉN GANG (basert på unik URN)")
    print()


if __name__ == '__main__':
    main()
