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
SEARCH_TYPE = "freetext"
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
            return {
                "status": "error",
                "message": "Search script failed",
                "error": result.stderr
            }

        # Read the generated CSV files
        pivot_file = f'historiske_spel_UNIKE_{SEARCH_TYPE}_{FROM_YEAR}_{TO_YEAR}.csv'
        detail_file = f'historiske_spel_DETALJER_{SEARCH_TYPE}_{FROM_YEAR}_{TO_YEAR}.csv'

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
    # Remove TOTAL row and column for cleaner visualization
    data_df = pivot_df.drop('TOTAL', axis=0, errors='ignore')
    data_df = data_df.drop('TOTAL', axis=1, errors='ignore')

    # Get years (columns)
    years = [int(col) for col in data_df.columns if str(col).isdigit()]
    years.sort()

    # Get top 10 newspapers by total articles
    newspaper_totals = data_df.sum(axis=1).sort_values(ascending=False)
    top_newspapers = newspaper_totals.head(10).index.tolist()

    # Prepare data for stacked bar chart (newspapers over time)
    newspaper_data = []
    for newspaper in top_newspapers:
        values = []
        for year in years:
            val = data_df.loc[newspaper, year] if year in data_df.columns else 0
            values.append(int(val) if pd.notna(val) else 0)

        newspaper_data.append({
            "label": newspaper,
            "data": values,
            "total": int(newspaper_totals[newspaper])
        })

    # Prepare data for yearly trend (total articles per year)
    yearly_totals = []
    for year in years:
        if year in data_df.columns:
            total = int(data_df[year].sum())
        else:
            total = 0
        yearly_totals.append(total)

    # Calculate statistics
    total_articles = sum(yearly_totals)
    total_newspapers = len(data_df)

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

    return {
        "years": years,
        "newspapers": newspaper_data,
        "yearlyTotals": yearly_totals,
        "pieData": pie_data,
        "statistics": {
            "totalArticles": total_articles,
            "totalNewspapers": total_newspapers,
            "topNewspapers": top_newspapers[:5],
            "dateRange": f"{min(years)}-{max(years)}"
        }
    }


@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('', 'index.html')


@app.route('/api/search', methods=['POST'])
def search():
    """Run search and return results as JSON"""
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
