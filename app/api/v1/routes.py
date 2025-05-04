from app.services.fetcher import fetch_network_data
from app.services.processor import process_data
from app.services.analytics import (
    plot_station_counts,
    summary_by_country,
    get_top_country,
    get_top_network
)
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)

def load_dashboard():
    networks = fetch_network_data()

    if not networks:
        logging.warning("No network data fetched.")
        return pd.DataFrame(), None, None, pd.DataFrame(), pd.DataFrame()

    df = process_data(networks)

    if df.empty:
        logging.warning("Processed DataFrame is empty.")
        return df, None, None, pd.DataFrame(), pd.DataFrame()

    try:
        bar_chart = plot_station_counts(df)
    except Exception as e:
        logging.error(f"Error generating bar chart: {e}")
        bar_chart = None

    try:
        summary = summary_by_country(df)
    except Exception as e:
        logging.error(f"Error generating summary table: {e}")
        summary = None

    try:
        top_country = get_top_country(df)
    except Exception as e:
        logging.error(f"Error getting top countries: {e}")
        top_country = pd.DataFrame()

    try:
        top_network = get_top_network(df)
    except Exception as e:
        logging.error(f"Error getting top networks: {e}")
        top_network = pd.DataFrame()

    return df, bar_chart, summary, top_country, top_network


