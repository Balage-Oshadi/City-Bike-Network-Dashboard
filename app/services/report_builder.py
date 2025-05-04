import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import os

from PIL import Image as PILImage
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from datetime import datetime


def save_bar_chart(df, filename):
    try:
        if 'name' not in df.columns or 'station_count' not in df.columns:
            raise ValueError("Missing required columns: 'name' or 'station_count'")

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(df['name'], df['station_count'])
        ax.set_title("Top Countries by Network Count")
        ax.set_ylabel("Networks")
        ax.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        fig.savefig(filename)
        plt.close(fig)

    except Exception as e:
        print(f"Bar chart error: {e}")
        with open(filename, "w") as f:
            f.write("Invalid chart placeholder")


def save_pie_chart(df, filename):
    try:
        if 'name' not in df.columns or 'station_count' not in df.columns:
            raise ValueError("Missing required columns: 'name' or 'station_count'")

        fig, ax = plt.subplots(figsize=(6, 6))
        ax.pie(df['station_count'], labels=df['name'], autopct='%1.1f%%', startangle=140)
        ax.set_title("Top Networks by Station Count")
        plt.tight_layout()
        fig.savefig(filename)
        plt.close(fig)

    except Exception as e:
        print(f"Pie chart error: {e}")
        with open(filename, "w") as f:
            f.write("Invalid chart placeholder")


def generate_pdf_report(df, top_country, total_networks, total_stations, top_network, top_country_networks_df,
                        world_map_fig=None, top_country_fig=None, top_networks_pie_fig=None,
                        include_summary=True, include_charts=True, include_map=True):

    doc = SimpleDocTemplate("final_report.pdf", pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("🚴 City Bike Network Report", styles["Title"]))
    story.append(Spacer(1, 12))

    # Summary block
    if include_summary:
        story.append(Paragraph(f"<b>Total Networks:</b> {total_networks}", styles["Normal"]))
        story.append(Paragraph(f"<b>Total Stations:</b> {total_stations}", styles["Normal"]))
        story.append(Paragraph(f"<b>Top Country:</b> {top_country}", styles["Normal"]))
        story.append(Paragraph(f"<b>Top Network:</b> {top_network}", styles["Normal"]))
        story.append(Spacer(1, 12))

    # === Charts Section ===
    if include_charts:
        # Bar Chart
        save_bar_chart(top_country_networks_df.head(10), "top_countries.png")
        story.append(Paragraph("📊 Top 10 Countries by Network Count", styles["Heading2"]))
        if os.path.exists("top_countries.png"):
            try:
                story.append(Image("top_countries.png", width=400, height=250))
            except Exception:
                story.append(Paragraph("⚠️ Failed to load 'top_countries.png'", styles["Normal"]))
        story.append(Spacer(1, 12))

        # Pie Chart
        save_pie_chart(top_country_networks_df.head(5), "top_networks_pie.png")
        story.append(Paragraph("🏆 Top 10 Networks by Station Count", styles["Heading2"]))
        if os.path.exists("top_networks_pie.png"):
            try:
                story.append(Image("top_networks_pie.png", width=400, height=250))
            except Exception:
                story.append(Paragraph("⚠️ Failed to load 'top_networks_pie.png'", styles["Normal"]))
        story.append(Spacer(1, 12))

    # === Map Section (Optional Placeholder) ===
    if include_map:
        story.append(Paragraph("🗺️ World Map of Bike Stations", styles["Heading2"]))
        story.append(Paragraph("📌 Map rendering is disabled on Streamlit Cloud due to system limitations.", styles["Normal"]))
        story.append(Spacer(1, 12))

    # Footer
    story.append(Spacer(1, 20))
    footer = Paragraph(
        f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} by City Bike Network Dashboard.",
        styles["Normal"]
    )
    story.append(footer)

    # Build PDF
    doc.build(story)

    return "final_report.pdf"
