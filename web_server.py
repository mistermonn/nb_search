#!/usr/bin/env python3
"""
Web server for NB Search - Visual solution
Runs the existing search.py script and provides a web interface with visualizations
"""

from flask import Flask, render_template, jsonify, send_from_directory, request
import subprocess
import pandas as pd
import json
import os
import sys
from pathlib import Path

app = Flask(__name__, static_folder='static', template_folder='templates')

# Configuration
SEARCH_SCRIPT = "search.py"
SEARCH_TYPE = "exact_phrase"  # Use exact_phrase for accurate results (not fulltext which gives too many hits)
FROM_YEAR = 2015
TO_YEAR = 2025
METADATA_FILE = "newspaper_metadata.csv"

# Load newspaper metadata (avis_id -> name, location, county)
def load_newspaper_metadata():
    """Load newspaper metadata from CSV file"""
    try:
        metadata_df = pd.read_csv(METADATA_FILE, encoding='utf-8-sig')
        # Create dictionary mapping: avis_id -> metadata
        metadata_dict = {}
        for _, row in metadata_df.iterrows():
            metadata_dict[row['avis_id']] = {
                'navn': row['avis_navn'],
                'by': row['by'],
                'fylke': row['fylke'],
                'lat': row['lat'],
                'lon': row['lon']
            }
        print(f"✅ Loaded metadata for {len(metadata_dict)} newspapers")
        return metadata_dict
    except Exception as e:
        print(f"⚠️  Could not load newspaper metadata: {e}")
        return {}

# Load metadata at startup
NEWSPAPER_METADATA = load_newspaper_metadata()

def run_search(search_term=None, from_year=None, to_year=None):
    """
    Run the existing search.py script with custom parameters and capture results
    Args:
        search_term: Search term (default: uses SEARCH_TERM from config)
        from_year: Start year (default: uses FROM_YEAR from config)
        to_year: End year (default: uses TO_YEAR from config)
    Returns: dict with status, data, and error info
    """
    # Use defaults if not provided
    if search_term is None:
        search_term = "historiske spel"
    if from_year is None:
        from_year = FROM_YEAR
    if to_year is None:
        to_year = TO_YEAR

    try:
        print(f"Running search.py with: '{search_term}', {from_year}-{to_year}...")

        # Build command with arguments
        cmd = [
            sys.executable, SEARCH_SCRIPT,
            '--search-term', search_term,
            '--from-year', str(from_year),
            '--to-year', str(to_year),
            '--search-type', SEARCH_TYPE
        ]

        # Run the search script
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )

        if result.returncode != 0:
            # Extract useful error info from stderr
            error_msg = result.stderr

            # Check for common errors
            if "api.nb.no" in error_msg.lower() or "connection" in error_msg.lower():
                friendly_msg = "Kunne ikke koble til Nasjonalbibliotekets API"
                suggestion = ("Mulige årsaker:\n"
                            "- Ingen internettforbindelse\n"
                            "- API'et er nede eller utilgjengelig\n"
                            "- Du mangler tilgang til api.nb.no\n\n"
                            "Prøv å søke om forskningstilgang på nb.no")
            elif "ingen resultater" in error_msg.lower() or "no results" in error_msg.lower():
                friendly_msg = "Søket returnerte ingen resultater"
                suggestion = "Prøv å endre søkeord eller utvide tidsperioden"
            else:
                friendly_msg = "Søket feilet"
                suggestion = ""

            return {
                "status": "error",
                "message": friendly_msg,
                "error": f"{suggestion}\n\nTeknisk info:\n{error_msg}"
            }

        # Read the generated CSV files
        # Note: search term "historiske spel" becomes "historiske_spel" in filename
        safe_search_term = search_term.replace(' ', '_').replace('"', '').replace("'", '')
        pivot_file = f'{safe_search_term}_UNIKE_{SEARCH_TYPE}_{from_year}_{to_year}.csv'
        detail_file = f'{safe_search_term}_DETALJER_{SEARCH_TYPE}_{from_year}_{to_year}.csv'

        if not os.path.exists(pivot_file):
            return {
                "status": "error",
                "message": "Pivot CSV file not found",
                "error": f"Expected file: {pivot_file}"
            }

        # Read pivot table
        pivot_df = pd.read_csv(pivot_file, encoding='utf-8-sig', index_col=0)

        # Read detailed data if available
        detail_df = None
        if os.path.exists(detail_file):
            detail_df = pd.read_csv(detail_file, encoding='utf-8-sig')

        # Convert to JSON-friendly format
        data = prepare_data_for_visualization(pivot_df, detail_df)

        return {
            "status": "success",
            "data": data,
            "message": "Search completed successfully"
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Search timed out (>2 minutes)",
            "error": "The search took too long. Try reducing the date range."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "Unexpected error",
            "error": str(e)
        }


def prepare_data_for_visualization(pivot_df, detail_df=None):
    """
    Convert pandas DataFrames to JSON structure for charts with proper newspaper names and county grouping
    """
    print(f"\n🔍 DEBUG prepare_data_for_visualization:")
    print(f"   pivot_df shape: {pivot_df.shape}")
    print(f"   pivot_df columns: {pivot_df.columns.tolist()}")
    print(f"   pivot_df index: {pivot_df.index.tolist()[:5]}...")  # First 5

    # Remove TOTAL row and column for cleaner visualization
    data_df = pivot_df.drop('TOTAL', axis=0, errors='ignore')
    data_df = data_df.drop('TOTAL', axis=1, errors='ignore')

    print(f"   After dropping TOTAL - shape: {data_df.shape}")
    print(f"   After dropping TOTAL - columns: {data_df.columns.tolist()}")

    # Get years (columns) - keep as strings to match column names!
    year_cols = [col for col in data_df.columns if str(col).isdigit()]
    year_cols.sort()  # Sort as strings
    years_int = [int(col) for col in year_cols]  # For display in frontend
    print(f"   Years found (strings): {year_cols}")
    print(f"   Years found (ints): {years_int}")

    # Calculate total articles per newspaper
    newspaper_totals = data_df.sum(axis=1).sort_values(ascending=False)

    # Get top 10 newspapers by total articles
    top_10_ids = newspaper_totals.head(10).index.tolist()

    # Map to proper names and prepare Top 10 list with coordinates
    top_10_list = []
    for i, avis_id in enumerate(top_10_ids, 1):
        metadata = NEWSPAPER_METADATA.get(avis_id, {})
        top_10_list.append({
            "rank": i,
            "avis_id": avis_id,
            "avis_navn": metadata.get('navn', avis_id.title()),
            "by": metadata.get('by', 'Ukjent'),
            "fylke": metadata.get('fylke', 'Ukjent'),
            "lat": metadata.get('lat', 60.0),
            "lon": metadata.get('lon', 10.0),
            "total": int(newspaper_totals[avis_id])
        })

    print(f"   Top 10 newspapers: {[n['avis_navn'] for n in top_10_list]}")

    # Prepare data for yearly trend (total articles per year)
    yearly_totals = []
    for year_col in year_cols:  # Use string column names!
        if year_col in data_df.columns:
            total = int(data_df[year_col].sum())
        else:
            total = 0
        yearly_totals.append(total)

    # Aggregate by county (fylke) for pie chart
    fylke_totals = {}
    for avis_id, total in newspaper_totals.items():
        metadata = NEWSPAPER_METADATA.get(avis_id, {})
        fylke = metadata.get('fylke', 'Ukjent')
        if fylke not in fylke_totals:
            fylke_totals[fylke] = 0
        fylke_totals[fylke] += int(total)

    # Convert to pie chart format and sort by value
    pie_data = []
    for fylke, value in sorted(fylke_totals.items(), key=lambda x: x[1], reverse=True):
        pie_data.append({
            "label": fylke,
            "value": value
        })

    # Calculate statistics
    total_articles = sum(yearly_totals)
    total_newspapers = len(data_df)
    total_counties = len(fylke_totals)

    print(f"   Yearly totals: {yearly_totals}")
    print(f"   Total articles: {total_articles}")
    print(f"   Total counties: {total_counties}")
    print(f"   County distribution: {list(fylke_totals.keys())}")

    result = {
        "years": years_int,  # Send integers for frontend display
        "yearlyTotals": yearly_totals,
        "top10": top_10_list,  # New: Top 10 list with coordinates for map
        "pieData": pie_data,  # Now shows county distribution
        "statistics": {
            "totalArticles": total_articles,
            "totalNewspapers": total_newspapers,
            "totalCounties": total_counties,
            "topNewspapers": [n['avis_navn'] for n in top_10_list[:5]],
            "dateRange": f"{min(years_int)}-{max(years_int)}" if years_int else "N/A"
        }
    }

    print(f"   Returning data with Top 10 newspapers and {len(pie_data)} counties")
    print()

    return result


@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('', 'index.html')


@app.route('/api/search', methods=['POST'])
def search():
    """Run search and return results as JSON"""
    # Get parameters from request
    params = request.get_json() or {}
    search_term = params.get('searchTerm', 'historiske spel')
    from_year = params.get('fromYear', FROM_YEAR)
    to_year = params.get('toYear', TO_YEAR)

    # Create safe filename
    safe_search_term = search_term.replace(' ', '_').replace('"', '').replace("'", '')

    # First check if CSV files already exist
    pivot_file = f'{safe_search_term}_UNIKE_{SEARCH_TYPE}_{from_year}_{to_year}.csv'

    if os.path.exists(pivot_file):
        # Use existing CSV files instead of running search again
        try:
            pivot_df = pd.read_csv(pivot_file, encoding='utf-8-sig', index_col=0)

            detail_file = f'{safe_search_term}_DETALJER_{SEARCH_TYPE}_{from_year}_{to_year}.csv'
            detail_df = None
            if os.path.exists(detail_file):
                detail_df = pd.read_csv(detail_file, encoding='utf-8-sig')

            data = prepare_data_for_visualization(pivot_df, detail_df)

            return jsonify({
                "status": "success",
                "data": data,
                "message": f"Bruker eksisterende søkeresultater for '{search_term}' ({from_year}-{to_year})"
            })
        except Exception as e:
            # If reading existing files fails, fall back to running search
            print(f"Failed to read existing files: {e}")
            pass

    # No existing files or reading failed - run search.py with custom parameters
    print(f"CSV files not found, running search for '{search_term}' ({from_year}-{to_year})...")
    search_result = run_search(search_term=search_term, from_year=from_year, to_year=to_year)

    if search_result['status'] == 'error':
        return jsonify(search_result)

    # Search succeeded, return the data
    return jsonify(search_result)


@app.route('/api/status')
def status():
    """Check if the server is running"""
    return jsonify({
        "status": "ok",
        "message": "NB Search Web Server is running"
    })


if __name__ == '__main__':
    # Try different ports if 5000 is in use
    import socket

    def find_free_port(start_port=5000, max_attempts=10):
        """Find a free port starting from start_port"""
        for port in range(start_port, start_port + max_attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port
            except OSError:
                continue
        return None

    port = find_free_port()

    if port is None:
        print("❌ Kunne ikke finne en ledig port!")
        print("   Prøv å stoppe andre programmer som bruker porter 5000-5010")
        sys.exit(1)

    print("=" * 80)
    print("NB SEARCH - WEB VISUALISERING")
    print("=" * 80)
    print(f"\nServeren starter på: http://localhost:{port}")
    print("\n✅ Åpne denne URL-en i nettleseren din for å se visualiseringen.")
    print("\nTrykk CTRL+C for å stoppe serveren.")
    print("=" * 80)
    print()

    # Check if search.py exists
    if not os.path.exists(SEARCH_SCRIPT):
        print(f"⚠️  ADVARSEL: {SEARCH_SCRIPT} ikke funnet!")
        print(f"   Sjekk at filen finnes i samme mappe som web_server.py")
        sys.exit(1)

    app.run(debug=True, host='0.0.0.0', port=port)
