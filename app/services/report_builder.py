import pandas as pd
import streamlit as st
import plotly.io as pio

from weasyprint import HTML
from datetime import datetime
from jinja2 import Template


def generate_pdf_report(df, top_country, total_networks, total_stations, top_network, top_country_networks_df,
                        world_map_fig, top_country_fig, top_networks_pie_fig):

    # === Save figures as static images ===
    world_map_fig_path = "world_map.png"
    top_country_fig_path = "top_countries.png"
    top_networks_pie_fig_path = "top_networks_pie.png"

    pio.write_image(world_map_fig, world_map_fig_path, format="png", width=1000, height=600)
    pio.write_image(top_country_fig, top_country_fig_path, format="png", width=800, height=500)
    pio.write_image(top_networks_pie_fig, top_networks_pie_fig_path, format="png", width=800, height=500)

    # === Convert DataFrame to list of dicts ===
    table_data = top_country_networks_df.to_dict(orient="records")

    # === Load and render HTML template ===
    with open("template.html", "r") as f:
        template = Template(f.read())

    rendered_html = template.render(
        total_networks=total_networks,
        total_stations=total_stations,
        top_country=top_country,
        top_network=top_network,
        generated_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        table_data=table_data,
        world_map_img=world_map_fig_path,
        bar_chart_img=top_country_fig_path,
        pie_chart_img=top_networks_pie_fig_path
    )

    # === Save HTML ===
    with open("final_report.html", "w") as f:
        f.write(rendered_html)

    # === Convert HTML to PDF ===
    pdf_path = "final_report.pdf"
    HTML("final_report.html").write_pdf(pdf_path)

    return pdf_path

