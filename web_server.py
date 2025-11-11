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
    Convert pandas DataFrames to JSON structure for charts
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

    # Get top 10 newspapers PER YEAR (not by total across all years)
    # This ensures each year shows its own top 10 newspapers
    top_newspapers_per_year = set()
    for year_col in year_cols:
        if year_col in data_df.columns:
            year_top10 = data_df[year_col].nlargest(10).index.tolist()
            top_newspapers_per_year.update(year_top10)

    # Convert to list and sort by total articles for consistent ordering
    top_newspapers = list(top_newspapers_per_year)
    newspaper_totals = data_df.sum(axis=1)
    top_newspapers.sort(key=lambda x: newspaper_totals[x], reverse=True)

    print(f"   Top newspapers across all years: {len(top_newspapers)} newspapers")
    print(f"   (Each year shows its own top 10)")

    # Prepare data for stacked bar chart (newspapers over time)
    newspaper_data = []
    for newspaper in top_newspapers:
        values = []
        for year_col in year_cols:  # Use string column names!
            val = data_df.loc[newspaper, year_col] if year_col in data_df.columns else 0
            values.append(int(val) if pd.notna(val) else 0)

        newspaper_data.append({
            "label": newspaper,
            "data": values,
            "total": int(newspaper_totals[newspaper])
        })

    # Prepare data for yearly trend (total articles per year)
    yearly_totals = []
    for year_col in year_cols:  # Use string column names!
        if year_col in data_df.columns:
            total = int(data_df[year_col].sum())
        else:
            total = 0
        yearly_totals.append(total)

    # Calculate statistics
    total_articles = sum(yearly_totals)
    total_newspapers = len(data_df)

    print(f"   Yearly totals: {yearly_totals}")
    print(f"   Total articles: {total_articles}")
    print(f"   Top newspapers: {top_newspapers}")

    # Prepare data for pie chart (ALL newspapers distribution)
    # Sort all newspapers by total articles for better visualization
    all_newspapers_sorted = newspaper_totals.sort_values(ascending=False)
    pie_data = []
    for newspaper in all_newspapers_sorted.index:
        pie_data.append({
            "label": newspaper,
            "value": int(all_newspapers_sorted[newspaper])
        })

    result = {
        "years": years_int,  # Send integers for frontend display
        "newspapers": newspaper_data,
        "yearlyTotals": yearly_totals,
        "pieData": pie_data,
        "statistics": {
            "totalArticles": total_articles,
            "totalNewspapers": total_newspapers,
            "topNewspapers": top_newspapers[:5],
            "dateRange": f"{min(years_int)}-{max(years_int)}" if years_int else "N/A"
        }
    }

    print(f"   Returning data with {len(newspaper_data)} newspapers")
    print(f"   Pie data entries: {len(pie_data)}")
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
