import plotly.express as px
import pandas as pd
import streamlit as st

from app.services.fetcher import fetch_network_details





def plot_station_counts(df):
    if df.empty or 'station_count' not in df.columns:
        return None

    df = df.copy()

    # Clean station_count: convert to numeric, drop missing, enforce > 0
    df['station_count'] = pd.to_numeric(df['station_count'], errors='coerce')
    df = df[df['station_count'].notnull()]
    df = df[df['station_count'] > 0]

    if df.empty:
        return None

    df = df.sort_values(by="station_count", ascending=True)
    return px.bar(
        df,
        x="station_count",
        y="name",
        orientation="h",
        title="Station Count per Network"
    )

def summary_by_country(df):
    return df.groupby("country")["station_count"].agg(["mean", "max", "count"]).reset_index()

def get_top_country(df):
    if "country" not in df.columns:
        print("No 'country' column in DataFrame.")
        return pd.DataFrame(columns=["country", "station_count"])
    if df.empty:
        print("DataFrame is empty.")
        return pd.DataFrame(columns=["country", "station_count"])

    country_df = df.groupby("country")["station_count"].sum().reset_index()
    return country_df.sort_values(by="station_count", ascending=False).head(5)

def get_top_network(df):
    if not df.empty:
        max_row = df.loc[df["station_count"].idxmax()]
        return f"{max_row['name']} ({max_row['station_count']} stations)"
    return "N/A"

def get_top_10_networks_by_station_count(networks: list) -> list:
    top_networks = []

    for net in networks:
        try:
            network_id = net.get("id")
            name = net.get("name", "Unknown")

            details = fetch_network_details(network_id)
            stations = details.get("stations", [])
            count = len(stations)

            top_networks.append({
                "name": name,
                "station_count": count
            })
        except Exception as e:
            print(f"⚠️ Failed to fetch stations for {network_id}: {e}")

    # Sort and return top 10
    return sorted(top_networks, key=lambda x: x["station_count"], reverse=True)[:10]







