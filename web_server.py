#!/usr/bin/env python3
"""
Web server for NB Search - Visual solution
Runs the existing search.py script and provides a web interface with visualizations
"""

from flask import Flask, render_template, jsonify, send_from_directory
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

def run_search():
    """
    Run the existing search.py script and capture results
    Returns: dict with status, data, and error info
    """
    try:
        print("Running search.py...")
        # Run the search script
        result = subprocess.run(
            [sys.executable, SEARCH_SCRIPT],
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
        safe_search_term = "historiske_spel"
        pivot_file = f'{safe_search_term}_UNIKE_{SEARCH_TYPE}_{FROM_YEAR}_{TO_YEAR}.csv'
        detail_file = f'{safe_search_term}_DETALJER_{SEARCH_TYPE}_{FROM_YEAR}_{TO_YEAR}.csv'

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

    # Get top 10 newspapers by total articles
    newspaper_totals = data_df.sum(axis=1).sort_values(ascending=False)
    top_newspapers = newspaper_totals.head(10).index.tolist()

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

    # Prepare data for pie chart (top newspapers distribution)
    pie_data = []
    for newspaper in top_newspapers:
        pie_data.append({
            "label": newspaper,
            "value": int(newspaper_totals[newspaper])
        })

    # Add "Others" category
    others_total = newspaper_totals[~newspaper_totals.index.isin(top_newspapers)].sum()
    if others_total > 0:
        pie_data.append({
            "label": "Andre aviser",
            "value": int(others_total)
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
    # First check if CSV files already exist
    safe_search_term = "historiske_spel"
    pivot_file = f'{safe_search_term}_UNIKE_{SEARCH_TYPE}_{FROM_YEAR}_{TO_YEAR}.csv'

    if os.path.exists(pivot_file):
        # Use existing CSV files instead of running search again
        try:
            pivot_df = pd.read_csv(pivot_file, encoding='utf-8-sig', index_col=0)

            detail_file = f'{safe_search_term}_DETALJER_{SEARCH_TYPE}_{FROM_YEAR}_{TO_YEAR}.csv'
            detail_df = None
            if os.path.exists(detail_file):
                detail_df = pd.read_csv(detail_file, encoding='utf-8-sig')

            data = prepare_data_for_visualization(pivot_df, detail_df)

            return jsonify({
                "status": "success",
                "data": data,
                "message": "Bruker eksisterende søkeresultater (CSV-filer funnet)"
            })
        except Exception as e:
            # If reading existing files fails, fall back to running search
            pass

    # No existing files or reading failed, run search
    result = run_search()
    return jsonify(result)


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
