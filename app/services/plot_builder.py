import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def plot_world_station_map(df: pd.DataFrame, filters_applied: bool = False):
    try:
        if df.empty or not {"latitude", "longitude"}.issubset(df.columns):
            return None

        df_map = df.dropna(subset=["latitude", "longitude"]).copy()

        # Ensure 'name' exists
        df_map["name"] = df_map.get("name", "Unknown")

        # Initialize hover data
        hover_data = {
            "latitude": True,
            "longitude": True
        }

        if filters_applied:
            # Initialize columns if not present or NaN
            if "free_bikes" not in df_map.columns:
                df_map["free_bikes"] = 0
            if "empty_slots" not in df_map.columns:
                df_map["empty_slots"] = 0

            # Normalize values to avoid NaNs
            df_map["free_bikes"] = pd.to_numeric(df_map["free_bikes"], errors="coerce").fillna(0).astype(int)
            df_map["empty_slots"] = pd.to_numeric(df_map["empty_slots"], errors="coerce").fillna(0).astype(int)

            hover_data["free_bikes"] = True
            hover_data["empty_slots"] = True

        fig = px.scatter_mapbox(
            df_map,
            lat="latitude",
            lon="longitude",
            hover_name="name",
            hover_data=hover_data,
            zoom=1,
            height=500
        )

        fig.update_layout(
            mapbox_style="carto-positron",
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            uirevision='static'
        )

        return fig

    except Exception as e:
        print(f" Error in plot_world_station_map(): {e}")
        return None


def generate_country_summary(filtered_df, fetch_func):
    summary_by_country = []

    grouped = filtered_df.groupby("country")
    for country, group in grouped:
        total_stations = 0
        total_free_bikes = 0
        total_empty_slots = 0
        detailed_rows = []

        for _, row in group.iterrows():
            try:
                network_id = row["id"]
                details = fetch_func(network_id)

                if details:
                    stations = details.get("stations", [])
                    station_count = len(stations)
                    free_bikes = sum(s.get("free_bikes") or 0 for s in stations)
                    empty_slots = sum(s.get("empty_slots") or 0 for s in stations)
                else:
                    station_count = free_bikes = empty_slots = 0

                total_stations += station_count
                total_free_bikes += free_bikes
                total_empty_slots += empty_slots

                detailed_rows.append({
                    "Network": row["name"],
                    "Stations": station_count,
                    "Free Bikes": free_bikes,
                    "Empty Slots": empty_slots,
                    "Lat": row.get("latitude", 0),
                    "Lon": row.get("longitude", 0)
                })

            except Exception as e:
                detailed_rows.append({
                    "Network": row["name"],
                    "Error": str(e)
                })

        summary_by_country.append({
            "country": country,
            "stations": total_stations,
            "free_bikes": total_free_bikes,
            "empty_slots": total_empty_slots,
            "details": detailed_rows
        })

    return summary_by_country


def render_global_network_donut_chart(selected_network, enriched_df, full_df):
    """
    Renders a donut chart showing the selected network's station percentage.

    Args:
        selected_network (str): The name of the selected network.
        enriched_df (pd.DataFrame): The filtered/enriched dataframe.
        full_df (pd.DataFrame): The original enriched full dataset.

    Returns:
        go.Figure: A Plotly donut chart figure.
    """
    selected = enriched_df[enriched_df["name"] == selected_network]
    full_total = full_df["station_count"].sum()
    selected_count = selected["station_count"].sum()

    percent = round((selected_count / full_total) * 100, 2) if full_total > 0 else 0

    fig = go.Figure(data=[go.Pie(
        labels=["Selected Network", "Other Networks"],
        values=[selected_count, full_total - selected_count],
        hole=0.7,
        marker_colors=["#2ecc71", "#555"],
        textinfo="none"
    )])

    fig.add_annotation(
        text=f"<b>{percent} %</b>",
        font_size=28,
        showarrow=False,
        x=0.5, y=0.5
    )

    fig.update_layout(
        showlegend=False,
        paper_bgcolor="#111",
        plot_bgcolor="#111",
        margin=dict(t=0, b=0, l=0, r=0),
        height=300
    )

    return fig


def render_network_donut_chart(selected_network, selected_country, full_df):
    """
    Renders a donut chart showing how much a selected network contributes to 
    the total station count in its specific country.

    Args:
        selected_network (str): The name of the selected network.
        selected_country (str): The 2-letter country code.
        full_df (pd.DataFrame): The full enriched dataframe.

    Returns:
        go.Figure: A Plotly donut chart figure.
    """
    country_df = full_df[full_df["country"] == selected_country]
    selected = country_df[country_df["name"] == selected_network]

    country_total = country_df["station_count"].sum()
    network_count = selected["station_count"].sum()

    percent = round((network_count / country_total) * 100, 2) if country_total > 0 else 0

    fig = go.Figure(data=[go.Pie(
        labels=["Selected Network", "Other Networks in Country"],
        values=[network_count, country_total - network_count],
        hole=0.7,
        marker_colors=["#2ecc71", "#555"],
        textinfo="none"
    )])

    fig.add_annotation(
        text=f"<b>{percent}%</b>",
        font_size=28,
        showarrow=False,
        x=0.5, y=0.5
    )

    fig.update_layout(
        showlegend=False,
        paper_bgcolor="#111",
        plot_bgcolor="#111",
        margin=dict(t=0, b=0, l=0, r=0),
        height=300
    )

    return fig


def plot_network_distribution(df):
    counts = df["country"].value_counts().reset_index()
    counts.columns = ["country", "network_count"]
    return px.pie(counts, names="country", values="network_count", title="Networks Distribution by Country")

def plot_station_map(network, selected_station_name=None):
    if not network or 'stations' not in network:
        return None

    df = pd.DataFrame(network['stations'])
    df = df.dropna(subset=['latitude', 'longitude'])

    # Optional: zoom to a selected station
    if selected_station_name:
        df = df[df["name"] == selected_station_name]
        zoom = 13
    else:
        zoom = 1  # world view

    fig = px.scatter_mapbox(
        df,
        lat="latitude",
        lon="longitude",
        hover_name="name",
        hover_data={
            "free_bikes": True,
            "empty_slots": True,
            "latitude": True,
            "longitude": True
        },
        zoom=zoom,
        height=500
    )
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig

def plot_station_map_all_networks(networks_data, selected_network_id=None, selected_station_name=None):
    stations = []

    for network in networks_data:
        if selected_network_id and network.get("id") != selected_network_id:
            continue
        for s in network.get("stations", []):
            s["network_id"] = network.get("id")
            s["network_name"] = network.get("name")
            stations.append(s)

    df = pd.DataFrame(stations)
    df = df.dropna(subset=["latitude", "longitude"])

    if selected_station_name:
        df = df[df["name"] == selected_station_name]
        zoom = 13
    elif selected_network_id:
        zoom = 4
    else:
        zoom = 1

    fig = px.scatter_mapbox(
        df,
        lat="latitude",
        lon="longitude",
        hover_name="name",
        hover_data={
            "network_name": True,
            "free_bikes": True,
            "empty_slots": True,
            "latitude": True,
            "longitude": True
        },
        zoom=zoom,
        height=550
    )
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig

