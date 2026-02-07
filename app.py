# app.py

import streamlit as st
from urllib.parse import urlparse, parse_qs
from datetime import date
import pandas as pd

from core.api import XtreamAPI
from core.extractor import extract_series_inventory
from core.exporters import export_inventory_csv


def parse_xtream_url(url):
    parsed = urlparse(url)
    q = parse_qs(parsed.query)

    u = q.get("username", [None])[0]  # Get username from URL query
    p = q.get("password", [None])[0]  # Get password from URL query

    if not u or not p:
        return None, None, None

    host = f"{parsed.scheme}://{parsed.netloc}"  # Construct host URL
    return host, u, p


st.set_page_config("Xtream Inventory", "📊")
st.title("📊 Xtream Series Inventory Extractor & CSV Comparator")

# =========================
# Section 1: Xtream Extraction
# =========================
st.header("🚀 Extract Inventory from Xtream")
xtream_url = st.text_input("Xtream URL")  # Input for Xtream URL
server_label = st.text_input("Server Label (optional)")  # Optional server label

if st.button("Extract Inventory"):  # Trigger extraction
    host, u, p = parse_xtream_url(xtream_url)

    if not all([host, u, p]):
        st.error("Invalid Xtream URL")  # Show error if URL invalid
        st.stop()

    api = XtreamAPI(host, u, p)

    progress = st.progress(0)  # Initialize progress bar

    def update_progress(done, total):
        progress.progress(done / total)  # Update progress bar

    with st.spinner("Extracting series inventory..."):
        rows = extract_series_inventory(
            host,
            api,
            progress_cb=update_progress
        )

    if not rows:
        st.warning("No data extracted")  # Warn if nothing extracted
        st.stop()

    csv_text = export_inventory_csv(rows)

    today = date.today().isoformat()
    server_name = server_label.strip() or urlparse(host).netloc
    filename = f"xtream_inventory__{server_name}__{today}.csv"  # Construct CSV filename

    st.success(f"Done ✔️  ({len(rows)} rows)")  # Show success message
    st.download_button(
        "⬇️ Download CSV",
        csv_text,
        file_name=filename,
        mime="text/csv"
    )


# =========================
# Section 2: CSV Comparison by Series, Season & Category
# =========================
st.header("🆚 Compare CSVs by Series, Season & Category")
st.write("Upload reference CSV and server CSV to find missing episodes per series and season:")

ref_file = st.file_uploader("Reference CSV", type=["csv"], key="ref_csv")
server_file = st.file_uploader("Server CSV", type=["csv"], key="server_csv")

if ref_file and server_file:
    df_ref = pd.read_csv(ref_file)
    df_server = pd.read_csv(server_file)

    # Define Xtream CSV columns
    series_col = "series_name"
    season_col = "season"
    episodes_col = "episodes_count"
    category_col = "category_name"

    # Group by series, season, and category, sum episodes_count
    ref_grouped = df_ref.groupby([series_col, season_col, category_col])[episodes_col].sum().reset_index(name="ref_episodes")
    server_grouped = df_server.groupby([series_col, season_col])[episodes_col].sum().reset_index(name="server_episodes")

    # Merge reference and server data
    merged = ref_grouped.merge(server_grouped, on=[series_col, season_col], how="left")
    merged["server_episodes"] = merged["server_episodes"].fillna(0).astype(int)

    # Calculate missing episodes
    merged["episodes_missing"] = merged["ref_episodes"] - merged["server_episodes"]

    # Keep only series-season combinations with missing episodes
    missing_series = merged[merged["episodes_missing"] > 0]

    st.write(f"Number of series-season combinations missing episodes: {len(missing_series)}")
    st.dataframe(missing_series)

    # Download CSV of missing episodes
    csv_missing = missing_series.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download CSV Missing Episodes with Category",
        data=csv_missing,
        file_name="missing_episodes_with_category.csv",
        mime="text/csv"
    )
