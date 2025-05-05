import pandas as pd
import logging
import streamlit as st
import os
from app.services.fetcher import fetch_network_details

logging.basicConfig(level=logging.INFO)

def process_data(networks):
    processed = []

    for idx, net in enumerate(networks):
        try:
            location = net.get("location", {})
            extra = net.get("extra", {})

            row = {
                "id": net.get("id", f"unknown-{idx}"),
                "name": net.get("name", "Unknown"),
                "city": location.get("city", "Unknown"),
                "country": location.get("country", None),
                "latitude": location.get("latitude", None),
                "longitude": location.get("longitude", None),
                "station_count": extra.get("slots") if isinstance(extra.get("slots"), (int, float)) else 0
            }

            processed.append(row)

        except Exception as e:
            logging.warning(f"Skipping entry {idx} due to error: {e}")
            continue

    df = pd.DataFrame(processed)

    required_columns = ["country", "latitude", "longitude"]
    if all(col in df.columns for col in required_columns):
        df = df.dropna(subset=required_columns)
    else:
        logging.warning(f"One or more required columns missing: {required_columns}")

    if "station_count" in df.columns:
        df["station_count"] = pd.to_numeric(df["station_count"], errors='coerce').fillna(0).astype(int)
    else:
        logging.warning("Missing 'station_count' column; creating with default value 0.")
        df["station_count"] = 0

    return df

CACHE_FILE = "cached_station_data.csv"

@st.cache_data(show_spinner="🔄 Fetching live station data...", max_entries=1)
def enrich_with_station_data(df: pd.DataFrame) -> pd.DataFrame:
    try:
        df = df.copy()
        df["station_count"] = 0
        df["free_bikes"] = 0
        df["empty_slots"] = 0

        for idx, row in df.iterrows():
            network_id = row.get("id")
            if not network_id:
                continue

            details = fetch_network_details(network_id)
            stations = details.get("stations", [])

            df.at[idx, "station_count"] = len(stations)
            df.at[idx, "free_bikes"] = sum(int(s.get("free_bikes") or 0) for s in stations)
            df.at[idx, "empty_slots"] = sum(int(s.get("empty_slots") or 0) for s in stations)

        df.to_csv(CACHE_FILE, index=False)
        return df

    except Exception as e:
        st.warning(f" Live data failed: {e}")

        if os.path.exists(CACHE_FILE):
            st.info(" Loading from cached data...")
            return pd.read_csv(CACHE_FILE)
        else:
            st.error(" No live data and no cached fallback available.")
            return pd.DataFrame()


# === Enrich full dataset once and cache it for static metrics ===
@st.cache_data(show_spinner=" Preparing static enriched dataset...", max_entries=1)
def enrich_static_data():
    from app.api.v1.routes import load_dashboard
    base_df, *_ = load_dashboard()
    enriched_df = enrich_with_station_data(base_df)
    return enriched_df
