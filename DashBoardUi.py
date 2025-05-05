import streamlit as st
import pandas as pd
import plotly.express as px
import io

from app.api.v1.routes import load_dashboard
from app.services.fetcher import fetch_network_details
from app.services.report_builder import generate_pdf_report
from app.services.pagination import render_pagination_ui
from app.services.processor import enrich_with_station_data
from app.services.analytics import get_top_10_networks_by_station_count
from app.services.plot_builder import plot_world_station_map, generate_country_summary, render_global_network_donut_chart, render_network_donut_chart,  plot_station_map, plot_station_map_all_networks



# Configure wkhtmltopdf path for Docker
#config = pdfkit.configuration(wkhtmltopdf="/usr/bin/wkhtmltopdf")
#pdfkit.from_file("template.html", "report.pdf", configuration=config)


#html = "<h1>Bike Network Report</h1><p>Generated successfully.</p>"
#pdfkit.from_string(html, "report.pdf", configuration=config)



# === Page configuration === 
st.set_page_config(page_title="City Bike Network Dashboard", layout="wide", page_icon="🚴",initial_sidebar_state="expanded")



# === Load Dataset Before Sidebar ===
df, plot_bar_chart, summary_table, top_country, top_network = load_dashboard()


# === Sidebar Filters ===
with st.sidebar:
    st.sidebar.title("🚴 City Bike Network Dashboard")

    # Prepare options
    country_options = ["ALL"] + sorted(df["country"].dropna().unique())
    selected_country = st.selectbox("Select Country Code", country_options, index=0, placeholder="Type a country code")

    # Dynamic networks based on selected country
    if selected_country == "ALL":
        network_options = ["ALL"] + sorted(df["name"].dropna().unique())
    else:
        network_options = ["ALL"] + sorted(df[df["country"] == selected_country]["name"].dropna().unique())

    selected_network = st.selectbox("Select Network Name", network_options, index=0, placeholder="Type a network")

    sort_by = st.selectbox("Sort By", ["", "name", "city", "station count"], index=0)


# === Apply Filter Logic ===
filtered_df = df.copy()

filters_applied = (
    selected_country != "ALL" or
    selected_network != "ALL" or
    sort_by != ""
)

if selected_country != "ALL":
    filtered_df = filtered_df[filtered_df["country"] == selected_country]

if selected_network != "ALL":
    filtered_df = filtered_df[filtered_df["name"] == selected_network]

if sort_by:
    filtered_df = filtered_df.sort_values(by=sort_by)

# === Only enrich if filters are active ===
enriched_df = enrich_with_station_data(filtered_df) if filters_applied else df.copy()

# === Enrich Full Data Once (for static metrics) ===
enriched_full_df = enrich_with_station_data(df)

# === Prepare Static Metrics ===
total_networks = len(enriched_full_df)
total_stations = enriched_full_df["station_count"].sum()

# Top country by total stations
top_country_df = (
    enriched_full_df.groupby("country")["station_count"]
    .sum()
    .reset_index()
    .sort_values(by="station_count", ascending=False)
)
top_country_name = top_country_df.iloc[0]["country"]

# Top network by total stations (aggregated)
top_network_df = (
    enriched_full_df.groupby("name")["station_count"]
    .sum()
    .reset_index()
    .sort_values(by="station_count", ascending=False)
)
top_network_name = top_network_df.iloc[0]["name"]



filtered_summary_df = pd.DataFrame()
try:
    summaries = generate_country_summary(df[df["country"] == top_country_name], fetch_network_details)
    if summaries:
        filtered_summary_df = pd.DataFrame(summaries[0]["details"]).sort_values(by="Free Bikes", ascending=False)
except Exception as e:
    st.warning(f"Could not prepare filtered summary data for report: {e}")

# === Prepare Visuals for PDF Generation ===
world_map_figure = plot_world_station_map(enriched_df, filters_applied=filters_applied)

country_counts = df["country"].value_counts().head(10)
top_country_bar_figure = px.bar(
    x=country_counts.values,
    y=country_counts.index,
    orientation="h",
    labels={"x": "Network Count", "y": "Country"},
    text=country_counts.values,
    title=None
)
top_country_bar_figure.update_traces(textposition="outside", marker_color="#66CCFF")
top_country_bar_figure.update_layout(plot_bgcolor="#111", paper_bgcolor="#111", font_color="white")

top_networks = get_top_10_networks_by_station_count(df.to_dict(orient="records"))
names = [n["name"] for n in top_networks]
counts = [n["station_count"] for n in top_networks]
top_networks_pie_figure = px.pie(
    names=names,
    values=counts,
    hole=0.4,
    color_discrete_sequence=px.colors.sequential.Blues,
)
top_networks_pie_figure.update_layout(
    showlegend=True,
    paper_bgcolor="#111",
    plot_bgcolor="#111",
    font_color="white"
)

# Prepare df with correct structure for matplotlib
country_counts = df["country"].value_counts().head(10)
top_country_networks_df = pd.DataFrame({
    "name": country_counts.index,
    "station_count": country_counts.values
})

# === Generate Report Button in Sidebar ===
with st.sidebar:
    if st.button("Generate Report"):
        try:
            pdf_path = generate_pdf_report(
                df=df,
                top_country=top_country_name,
                total_networks=total_networks,
                total_stations=total_stations,
                top_network=top_network_name,
                top_country_networks_df=top_country_networks_df,
                world_map_fig=world_map_figure,
                top_country_fig=top_country_bar_figure,        # optional: still passed but unused in matplotlib mode
                top_networks_pie_fig=top_networks_pie_figure   # optional: still passed but unused in matplotlib mode
            )
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="Download PDF Report",
                    data=f,
                    file_name="Bike_Network_Report.pdf",
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"Report generation failed: {e}")





# === Modal UI Logic ===
if st.session_state.get("show_report_modal", False):
    st.markdown("""
        <style>
        .overlay {
            position: fixed;
            top: 0; left: 0;
            width: 100vw; height: 100vh;
            background: rgba(0, 0, 0, 0.6);
            z-index: 9990;
        }
        .modal {
            position: fixed;
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            background-color: #222;
            padding: 30px;
            border-radius: 12px;
            color: white;
            z-index: 9999;
            width: 400px;
            box-shadow: 0 0 20px rgba(255,255,255,0.3);
        }
        </style>
        <div class="overlay"></div>
        <div class="modal">
    """, unsafe_allow_html=True)

    st.markdown("### Select Report Sections")

    include_summary = st.checkbox(" Include Global Summary", value=True)
    include_charts = st.checkbox("Include Top Charts", value=True)
    include_map = st.checkbox("Include World Map", value=True)

    generate = st.button(" Download Report as PDF")
    cancel = st.button("Cancel")

    st.markdown("</div>", unsafe_allow_html=True)

    if cancel:
        st.session_state.show_report_modal = False

    if generate:
        st.session_state.generate_pdf = {
            "summary": include_summary,
            "charts": include_charts,
            "map": include_map
        }
        st.session_state.show_report_modal = False




if st.session_state.get("generate_pdf"):
    selected = st.session_state.generate_pdf
    st.success("Generating PDF...")

    try:
        pdf_path = generate_pdf_report(
            df=df,
            top_country=top_country_name,
            total_networks=total_networks,
            total_stations=total_stations,
            top_network=top_network_name,
            top_country_networks_df=filtered_summary_df if selected["summary"] else pd.DataFrame(),
            world_map_fig=world_map_figure if selected["map"] else None,
            top_country_fig=top_country_bar_figure if selected["charts"] else None,
            top_networks_pie_fig=top_networks_pie_figure if selected["charts"] else None,
            include_summary=selected["summary"],
            include_charts=selected["charts"],
            include_map=selected["map"]
        )

        with open(pdf_path, "rb") as f:
            st.download_button("Click to Download Your PDF Report", f, file_name="CityBike_Report.pdf")

    except Exception as e:
        st.error(f"Error while generating the report: {e}")

    del st.session_state["generate_pdf"]





st.markdown("""
    <div style='font-size: 30px; font-weight: bold; color: white; text-align:center; padding: 30px 0 10px 0;'>
         Global Bike Network Overview & Insights
    </div>
""", unsafe_allow_html=True)

# Create two side-by-side columns
left_col, right_col = st.columns([1,2])

# Global Bike Network Summary (LEFT COLUMN)
with left_col:

    # === Animated & Styled Metric Cards Section ===
    
    # Center container in column
    st.markdown("""
        <div style="display: flex; justify-content: center; align-items: center; flex-direction: column; padding-top: 20px;">
    """, unsafe_allow_html=True)
    
    # Inject Enhanced Animation CSS for Cards
    st.markdown("""
        <style>
        .metric-card-container {
            display: flex;
            justify-content: center;
            align-items: center;
            flex-wrap: wrap;
            gap: 24px;
            padding: 10px;
            margin: 0 auto;
            //margin-bottom: 20px;
        }
        .metric-card {
            background-color: #222;
            padding: 24px 20px;
            margin-bottom: 20px; /* vertical spacing */
            border-radius: 14px;
            text-align: center;
            width: 230px;
            min-height: 120px;
            color: white;
            opacity: 0;
            transform: scale(0.95);
            animation: bounceFadeIn 0.6s ease-in-out forwards;
            animation-fill-mode: forwards; /* <== ensures it keeps the final state */
            box-shadow: 0 6px 16px rgba(0,0,0,0.25);
            transition: transform 0.25s ease, box-shadow 0.25s ease;
        }

        .metric-card:nth-child(1) { animation-delay: 0s; }
        .metric-card:nth-child(2) { animation-delay: 0.1s; }
        .metric-card:nth-child(3) { animation-delay: 0.2s; }
        .metric-card:nth-child(4) { animation-delay: 0.3s; }

        .metric-card:hover {
            transform: scale(1.02);
            box-shadow: 0 10px 24px rgba(0,0,0,0.4);
            background-color: #333;
        }

        .metric-title {
            color: #bbb;
            font-size: 15px;
            margin-bottom: 10px;
        }

        .metric-value {
            font-size: 30px;
            font-weight: 700;
            color: #ffffff;
        }

        @keyframes bounceFadeIn {
            0% {
                opacity: 0;
                transform: scale(0.9) translateY(20px);
            }
            60% {
                opacity: 1;
                transform: scale(1.05) translateY(0px);
            }
            100% {
                opacity: 1;
                transform: scale(1) translateY(0);
            }
        }
                
        /* === Responsive for Phone: Show 2 per row === */
        @media (max-width: 600px) {
            .metric-card {
                flex: 1 1 calc(50% - 24px); /* two cards per row */
            }
        }
        </style>
    """, unsafe_allow_html=True)

    # Data for cards
    metrics = [
        ("Total Networks", total_networks),
        ("Top Country", top_country_name),
        ("Top Network", top_network_name),
        ("Total Stations", total_stations)
    ]

    st.markdown("<div style='width: 100%; display: flex; justify-content: center;'>", unsafe_allow_html=True)

    # Render Cards
    st.markdown("<div class='metric-card-container'>", unsafe_allow_html=True)

    for title, value in metrics:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">{title}</div>
                <div class="metric-value">{value}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)



# Country and Network Insights (RIGHT COLUMN)
with right_col:


    # === Middle Bar Charts (Static, Unfiltered) ===

    col1, col2 = st.columns(2)

    # Bar 1: Top 10 Countries by Network Count
    with col1:
        with st.container():
            st.markdown("""
            <div style="background-color:#222; padding:20px; border-radius:10px;">
                <div style="color:white; text-align:center; font-size: 20px; font-weight: bold; padding:10px;'"> Top 10 Countries by Network Count</div>
            """, unsafe_allow_html=True)

            try:
                if "country" in df.columns and not df.empty:
                    country_counts = df["country"].value_counts().head(10)

                    fig = px.bar(
                        x=country_counts.values,
                        y=country_counts.index,
                        orientation="h",
                        labels={"x": "Network Count", "y": "Country"},
                        text=country_counts.values,
                        title=None
                    )

                    fig.update_traces(textposition="outside", marker_color="#66CCFF")
                    fig.update_layout(plot_bgcolor="#111", paper_bgcolor="#111", font_color="white")

                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

                else:
                    st.info("No country data available to display.")
            except Exception as e:
                st.warning(f"Error displaying static country chart: {e}")
            st.markdown("</div>", unsafe_allow_html=True)

    # Pie Chart: Top 10 Networks by Station Count
    with col2:
        with st.container():
            st.markdown("""
            <div style="background-color:#222; padding:20px; border-radius:10px;">
                <div style="color:white; text-align:center; font-size: 20px; font-weight: bold; padding:10px;'"> Top 10 Networks by Station Count</div>
            """, unsafe_allow_html=True)

            try:
                top_networks = get_top_10_networks_by_station_count(df.to_dict(orient="records"))

                if top_networks:
                    names = [n["name"] for n in top_networks]
                    counts = [n["station_count"] for n in top_networks]

                    fig = px.pie(
                        names=names,
                        values=counts,
                        hole=0.4,
                        color_discrete_sequence=px.colors.sequential.Blues,
                    )

                    fig.update_layout(
                        showlegend=True,
                        paper_bgcolor="#111",
                        plot_bgcolor="#111",
                        font_color="white"
                    )

                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.info("No station data available to display.")
            except Exception as e:
                st.error(f" Error displaying pie chart for top networks: {e}")
            st.markdown("</div>", unsafe_allow_html=True)



# === Combined: World Map + Top Countries with Flags ===
st.markdown("""
        <div style='font-size: 30px; font-weight: bold; color: white; text-align:center;padding:20px;'>
             World Map and Top Countries Overview
        </div>
    """, unsafe_allow_html=True)

# Add spacing between rows
st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

map_col, flag_col = st.columns([2, 1])  # Adjust width ratio

# === World Map ===
with map_col:
    with st.container():
        st.markdown("""
            <div style="background-color:#222; padding:20px; border-radius:10px;">
                <div style="color:white; text-align:center; font-size: 20px; font-weight: bold; padding:10px;'"> World Map of Bike Stations</div>
        """, unsafe_allow_html=True)

        # Add spacing between rows
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

        try:
            filters_applied = any([selected_network, selected_country, sort_by])
            if filters_applied:
                try:
                    enriched_df = enrich_with_station_data(filtered_df)
                except Exception as enrich_error:
                    st.warning(f"Could not enrich data with station stats: {enrich_error}")
                    enriched_df = filtered_df
            else:
                enriched_df = filtered_df

            fig = plot_world_station_map(enriched_df, filters_applied=filters_applied)

            if fig:
                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    zoom=7,
                    config={"scrollZoom": True}
                )
            else:
                st.warning("No data available to render the world map.")
        except Exception as e:
            st.error(f" An error occurred while displaying the world map:\n{e}")

        st.markdown("</div>", unsafe_allow_html=True)

# === Top 10 Countries by Network Count with Flags (Static) ===
with flag_col:
    with st.container():
        st.markdown("""
            <div style="background-color:#222; padding:20px; border-radius:10px;">
                <div style="color:white; text-align:center; font-size: 20px; font-weight: bold; padding:10px;'"> Top 10 Countries by Network Count with Flags</div>
                <div style="display: flex; justify-content: center;">
        """, unsafe_allow_html=True)

        try:
            if "country" in df.columns and not df.empty:
                top_countries = df["country"].value_counts().head(10)
                
                # Centered wrapper with fixed width
                st.markdown("<div style='display: flex;'>", unsafe_allow_html=True)
                col1, col2 = st.columns([1, 1])

                for idx, (country_code, count) in enumerate(top_countries.items()):
                    target_col = col1 if idx < 5 else col2

                    try:
                        if isinstance(country_code, str) and len(country_code) == 2:
                            flag_url = f"https://flagcdn.com/w40/{country_code.lower()}.png"
                            target_col.markdown(
                                f"<img src='{flag_url}' width='30' style='margin-right:10px'> "
                                f"**{country_code.upper()}** — {count} networks",
                                unsafe_allow_html=True
                            )
                        else:
                            target_col.markdown(f"**{country_code.upper()}** — {count} networks")
                    except Exception as inner_e:
                        target_col.warning(f"Error displaying flag for {country_code}: {inner_e}")
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("No 'country' data available to display top countries.")
        except Exception as e:
            st.warning(f"Error processing top countries: {e}")

        st.markdown("""
                </div> <!-- End centered wrapper -->
            </div> <!-- End outer card -->
        """, unsafe_allow_html=True)






filters_applied = (
    (selected_country and selected_country != "ALL") or
    (selected_network and selected_network != "ALL") or
    bool(sort_by)
)

if filters_applied:
    st.markdown(f"""
        <div style='font-size: 26px; font-weight: bold; color: white; text-align:center; padding: 20px 0 10px 0;'>
             Regional Network Analysis: {selected_country if selected_country != 'ALL' else 'All Countries'}
        </div>
    """, unsafe_allow_html=True)

    # Add spacing between rows
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
# === Networks by Station Count or Donut Chart ===

with col1:
    
    if selected_network != "ALL"and selected_country == "ALL":
        st.markdown("""
            <div style="background-color:#222; padding:20px; border-radius:10px;">
                <div style="color:white; text-align:center; font-size: 20px; font-weight: bold; padding:10px;'">📊 Station Distribution in Global Network</div>
        """, unsafe_allow_html=True)

        # Add spacing between rows
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

        try:
            fig = render_global_network_donut_chart(selected_network, enriched_df, enriched_full_df)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        except Exception as e:
            st.error(f"Error rendering donut chart: {e}")
    
    elif selected_network != "ALL" and selected_country != "ALL":
        st.markdown(f"""
            <div style="background-color:#222; padding:20px; border-radius:10px;">
                <div style="color:white; text-align:center; font-size: 20px; font-weight: bold; padding:10px;">
                     Network Contribution in {selected_country if selected_country != 'ALL' else 'All Countries'}
                </div>
            </div>
        """, unsafe_allow_html=True)

        
        try:
            donut_fig = render_network_donut_chart(selected_network, selected_country, enriched_full_df)
            st.plotly_chart(donut_fig, use_container_width=True, config={"displayModeBar": False})
        except Exception as e:
            st.error(f"Error rendering donut chart: {e}")

    elif filters_applied:
        st.markdown(f"""
            <div style="background-color:#222; padding:20px; border-radius:10px;">
                <div style="color:white; text-align:center; font-size: 20px; font-weight: bold; padding:10px;">
                     Top 15 Networks by Station Count in {selected_country if selected_country != 'ALL' else 'All Countries'}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        try:
            if "station_count" in df.columns and "name" in df.columns and not df.empty:
                source_df = enriched_df if "station_count" in enriched_df.columns and enriched_df["station_count"].sum() > 0 else df
                top_nets = source_df.nlargest(15, "station_count")

                fig = px.bar(
                    top_nets,
                    x="station_count",
                    y="name",
                    orientation="h",
                    labels={"station_count": "Stations", "name": "Network"}
                )

                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("No station or network data available to display.")
        except Exception as e:
            st.warning(f"Error displaying static top networks chart: {e}")

# === Filtered Summary by Country and Networks (Improved Layout with Live Data) ===
with col2:
    #if any([selected_network, selected_country, sort_by]):
    if filters_applied:
        st.markdown("""
            <div style="background-color:#222; padding:20px; border-radius:10px;">
                <div style="color:white; text-align:center; font-size: 20px; font-weight: bold; padding:10px;'"> Filtered Summary by Country and Networks</div>
        """, unsafe_allow_html=True)

        # Add spacing between rows
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        
        try:
            if not filtered_df.empty:
                summaries = generate_country_summary(filtered_df, fetch_network_details)

                for entry in summaries:
                    st.markdown(f"####  Country: **{entry['country']}**")

                    c1, c2, c3 = st.columns(3)
                    c1.metric("🚲 Stations", entry["stations"])
                    c2.metric("🔋 Free Bikes", entry["free_bikes"])
                    c3.metric("🚧 Empty Slots", entry["empty_slots"])

                    display_df = pd.DataFrame(entry["details"]).sort_values(by="Free Bikes", ascending=False)

                    with st.expander(f" Show networks in {entry['country']} ({len(display_df)} total)"):
                        # Set up pagination parameters
                        page_size = 5
                        total_items = len(display_df)
                        total_pages = (total_items + page_size - 1) // page_size

                        # Maintain current page state per country
                        #page_number = st.session_state.get(f"{entry['country']}_page", 1)
                        current_page = st.session_state.get("summary_page", 1)
                        total_pages = (len(display_df) - 1) 

                        # Update page number
                        #page_number = render_pagination_ui(page_number, total_pages, entry['country'])
                        #st.session_state[f"{entry['country']}_page"] = page_number
                        current_page = render_pagination_ui(current_page, total_pages, "summary")

                        # Optionally store it in session state
                        st.session_state["summary_page"] = current_page

                        # Slice the DataFrame for the current page
                        #start = (page_number - 1) * page_size
                        
                        start = (current_page - 1) * page_size
                        end = start + page_size
                        paginated_df = display_df.iloc[start:end]

                        # Show paginated data
                        st.dataframe(paginated_df, use_container_width=True)

                        # Download button for full data
                        csv = display_df.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            label=f" Download CSV for {entry['country']}",
                            data=csv,
                            file_name=f"{entry['country']}_bike_networks.csv",
                            mime="text/csv"
                        )
            else:
                st.info("No filtered data to display.")
        except Exception as e:
            st.error(f" Error generating country-level details: {e}")

















