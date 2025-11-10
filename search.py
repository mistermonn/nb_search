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

# KONFIGURASJON (Standardverdier - kan overstyres ved kjøring)
DEFAULT_SEARCH_TYPE = "exact_phrase"  # Alternativer: "fulltext", "freetext", "exact_phrase"
DEFAULT_SEARCH_TERM = "historiske spel"
DEFAULT_FROM_YEAR = 2015
DEFAULT_TO_YEAR = 2025
MAX_RESULTS = 2000
DEBUG_MODE = False  # Sett til True for å se debug-meldinger

# VIKTIG:
# - "fulltext" finner artikler med 'historiske' ELLER 'spel' (gir mange treff)
# - "exact_phrase" finner kun artikler med den eksakte frasen 'historiske spel' (anbefalt)


def get_user_input():
    """
    Spør brukeren om søkeparametere
    """
    print("=" * 80)
    print("KONFIGURASJON AV SØKET")
    print("=" * 80)
    print()

    # Søkeord
    print(f"Søkeord (standard: '{DEFAULT_SEARCH_TERM}'):")
    search_term = input("➤ ").strip()
    if not search_term:
        search_term = DEFAULT_SEARCH_TERM

    # Fra år
    print(f"\nFra år (standard: {DEFAULT_FROM_YEAR}):")
    from_year_input = input("➤ ").strip()
    if from_year_input:
        try:
            from_year = int(from_year_input)
        except ValueError:
            print(f"⚠️  Ugyldig årstall, bruker standard: {DEFAULT_FROM_YEAR}")
            from_year = DEFAULT_FROM_YEAR
    else:
        from_year = DEFAULT_FROM_YEAR

    # Til år
    print(f"\nTil år (standard: {DEFAULT_TO_YEAR}):")
    print("   (Inkluderer hele året, t.o.m. 31. desember)")
    to_year_input = input("➤ ").strip()
    if to_year_input:
        try:
            to_year = int(to_year_input)
        except ValueError:
            print(f"⚠️  Ugyldig årstall, bruker standard: {DEFAULT_TO_YEAR}")
            to_year = DEFAULT_TO_YEAR
    else:
        to_year = DEFAULT_TO_YEAR

    # Søketype
    print(f"\nSøketype (standard: {DEFAULT_SEARCH_TYPE}):")
    print("  1 = exact_phrase (anbefalt - eksakt frase)")
    print("  2 = fulltext (bred søk, kan gi mange treff)")
    print("  3 = freetext (fungerer ikke alltid)")
    search_type_input = input("➤ ").strip()

    if search_type_input == "1":
        search_type = "exact_phrase"
    elif search_type_input == "2":
        search_type = "fulltext"
    elif search_type_input == "3":
        search_type = "freetext"
    elif search_type_input == "":
        search_type = DEFAULT_SEARCH_TYPE
    else:
        print(f"⚠️  Ukjent valg, bruker standard: {DEFAULT_SEARCH_TYPE}")
        search_type = DEFAULT_SEARCH_TYPE

    print()
    print("=" * 80)
    print("SØKEPARAMETERE:")
    print("=" * 80)
    print(f"  Søkeord:   '{search_term}'")
    print(f"  Periode:   {from_year} til og med {to_year} (hele året)")
    print(f"  Søketype:  {search_type}")
    print("=" * 80)
    print()

    input("Trykk ENTER for å starte søket, eller Ctrl+C for å avbryte...")
    print()

    return search_term, from_year, to_year, search_type


def create_pivot_table(search_term, from_year, to_year, search_type="exact_phrase"):
    """
    Søk i NB's avisarkiv og lag pivottabell med duplikatkontroll
    """
    print("=" * 80)
    print("SØKER I NASJONALBIBLIOTEKETS AVISARKIV (MED DUPLIKATKONTROLL)")
    print("=" * 80)
    print(f"\nSøkeord: '{search_term}'")
    print(f"Søketype: {search_type}")
    print(f"Periode: {from_year} til og med {to_year} (inkluderer hele {to_year})")
    print(f"\nHenter data fra NB's API...")
    print("(Dette kan ta 30-60 sekunder)\n")
    
    try:
        # Create corpus based on search type
        if search_type == "fulltext":
            print("ℹ️  FULLTEXT: Søker i ALL OCR'et tekst")
            corpus = Corpus(
                doctype='digavis',
                fulltext=search_term,
                from_year=from_year,
                to_year=to_year,
                limit=MAX_RESULTS
            )
        elif search_type == "freetext":
            print("ℹ️  FREETEXT: Søker i indeksert fritekst")
            corpus = Corpus(
                doctype='digavis',
                freetext=search_term,
                from_year=from_year,
                to_year=to_year,
                limit=MAX_RESULTS
            )
        elif search_type == "exact_phrase":
            print("ℹ️  EXACT PHRASE: Søker etter eksakt frase")
            corpus = Corpus(
                doctype='digavis',
                fulltext=f'"{search_term}"',
                from_year=from_year,
                to_year=to_year,
                limit=MAX_RESULTS
            )
        else:
            print(f"❌ Ukjent søketype: {search_type}")
            sys.exit(1)
        
        # Get corpus data as DataFrame
        if DEBUG_MODE:
            print(f"🔍 DEBUG: Corpus objekt opprettet: {corpus}")
            print(f"🔍 DEBUG: Type corpus: {type(corpus)}")
            print(f"🔍 DEBUG: Corpus attributes: {dir(corpus)[:10]}...")  # Show first 10 attributes

        df = corpus.corpus

        if DEBUG_MODE:
            print(f"🔍 DEBUG: DataFrame type: {type(df)}")
            print(f"🔍 DEBUG: DataFrame shape: {df.shape if hasattr(df, 'shape') else 'N/A'}")
            print(f"🔍 DEBUG: DataFrame empty: {df.empty if hasattr(df, 'empty') else 'N/A'}")
            if hasattr(df, 'columns'):
                print(f"🔍 DEBUG: DataFrame kolonner: {df.columns.tolist()}")

        if df.empty:
            print("\n❌ Ingen resultater funnet i DataFrame.")
            if DEBUG_MODE:
                print("\n🔍 DEBUG INFO:")
                print(f"   - Søkeord: '{search_term}'")
                print(f"   - Søketype: {search_type}")
                print(f"   - Periode: {from_year}-{to_year}")
                print(f"   - Max resultater: {MAX_RESULTS}")
                print(f"   - DataFrame er tom selv om corpus er opprettet")
                print("\n💡 Mulige årsaker:")
                print("   1. API'et returnerer ingen treff for denne kombinasjonen")
                print("   2. Autentiseringsproblem (krever forskertilgang?)")
                print("   3. Søkeordet må formateres annerledes")
                print("   4. Tidsperioden har ingen data")
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
    print("\n")
    print("=" * 80)
    print("NASJONALBIBLIOTEKETS AVISSØK")
    print("=" * 80)
    print("💡 VIKTIG: Dette scriptet fjerner duplikater før telling")
    print()

    # Get user input
    try:
        search_term, from_year, to_year, search_type = get_user_input()
    except KeyboardInterrupt:
        print("\n\n⚠️  Søk avbrutt av bruker")
        sys.exit(0)

    result = create_pivot_table(search_term, from_year, to_year, search_type)

    # Check if search returned results
    if result is None:
        print("\n" + "=" * 80)
        print("SØKET GA INGEN RESULTATER")
        print("=" * 80)
        print("\n💡 Tips:")
        print("   - Prøv en annen søketype (fulltext, freetext, eller exact_phrase)")
        print("   - Sjekk at du har nettverkstilgang til api.nb.no")
        print("   - Sjekk søkeordet og tidsperioden")
        print()
        sys.exit(0)

    pivot, df_unique = result

    print("\n" + "=" * 80)
    print("FERDIG!")
    print("=" * 80)
    print(f"\n✓ Hver artikkel er telt KUN ÉN GANG (basert på unik URN)")
    print()


if __name__ == '__main__':
    main()
