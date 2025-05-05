import pandas as pd
import io
from datetime import datetime
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import matplotlib.pyplot as plt

from matplotlib import cm
from matplotlib.colors import Normalize

from reportlab.lib import colors

from reportlab.lib.colors import HexColor

from reportlab.platypus.flowables import HRFlowable



def matplotlib_bar_chart(df, width=450, height=170):
    try:
        fig, ax = plt.subplots(figsize=(8, 4), facecolor='#111111')
        ax.set_facecolor('#111111')

        bars = ax.barh(df['name'], df['station_count'], color='#00b4d8')

        # Add value labels (smaller font, right-aligned)
        for bar in bars:
            ax.text(
                bar.get_width() + 2, bar.get_y() + bar.get_height() / 2,
                f'{int(bar.get_width())}', va='center', color='white', fontsize=8
            )

        # Refined labels and layout
        ax.set_xlabel("Number of Networks", color='white', fontsize=9)
        ax.set_title("Top 10 Countries by Network Count", color='white', fontsize=11, weight='bold')
        ax.tick_params(axis='x', colors='white', labelsize=8)
        ax.tick_params(axis='y', colors='white', labelsize=8)

        # Remove unnecessary spines
        for spine in ax.spines.values():
            spine.set_visible(False)

        plt.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format='png', facecolor=fig.get_facecolor())
        buf.seek(0)
        plt.close(fig)

        return Image(buf, width=width, height=height)
    except Exception as e:
        return Paragraph(f" Could not render bar chart: {e}", getSampleStyleSheet()["Normal"])


def matplotlib_pie_chart(df, width=450, height=220):
    try:
        fig, ax = plt.subplots(figsize=(6.5, 4), facecolor='#111111')
        ax.set_facecolor('#111111')

        # Gradient from blue -> light
        norm = Normalize(vmin=df['station_count'].min(), vmax=df['station_count'].max())
        cmap = cm.get_cmap('Blues')
        colors = [cmap(norm(v)) for v in df['station_count']]

        wedges, texts, autotexts = ax.pie(
            df['station_count'],
            labels=None,
            autopct='%1.1f%%',
            startangle=140,
            colors=colors,
            wedgeprops=dict(width=0.25, edgecolor='#111111')
        )

        # Brighter, clearer legend
        ax.legend(
            wedges, df['name'],
            title="Top Networks",
            loc="center left",
            bbox_to_anchor=(1, 0.5),
            labelcolor='white',
            facecolor='#111111',
            edgecolor='#111111',
            fontsize=9,
            title_fontsize=10
        )

        plt.setp(autotexts, color='white', fontsize=9, weight='bold')
        ax.set_title("Top 10 Networks by Station Count", color='white', fontsize=11, weight='bold')

        plt.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format='png', facecolor=fig.get_facecolor(), dpi=150)
        buf.seek(0)
        plt.close(fig)

        return Image(buf, width=width, height=height)
    except Exception as e:
        return Paragraph(f" Could not render pie chart: {e}", getSampleStyleSheet()["Normal"])


def generate_pdf_report(df, top_country, total_networks, total_stations, top_network,
                        top_country_networks_df, world_map_fig=None,
                        top_country_fig=None, top_networks_pie_fig=None,
                        include_summary=True, include_charts=True, include_map=True):

    doc = SimpleDocTemplate("final_report.pdf", pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # === Add Title ===
    story.append(Paragraph(
        "<para align='center'><font size=16 color='#1d4ed8'><b>City Bike Network Report</b></font></para>",
        styles["Normal"]
    ))
    story.append(Spacer(1, 25))

    # === Heading style ===
    heading_style = ParagraphStyle(
        name="HeadingWithUnderline",
        fontSize=12,
        leading=16,
        spaceAfter=4,
        spaceBefore=16,
        textColor=colors.black,
        fontName="Helvetica-Bold"
    )

    # === Paragraph style for table labels ===
    summary_style = ParagraphStyle(
        name="SummaryText",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        spaceAfter=4
    )

    # === Proper Paragraph-wrapped summary content ===
    summary_data = [
        [Paragraph("<b>Total Networks:</b>", summary_style), str(total_networks)],
        [Paragraph("<b>Total Stations:</b>", summary_style), str(total_stations)],
        [Paragraph("<b>Top Country:</b>", summary_style), top_country],
        [Paragraph("<b>Top Network:</b>", summary_style), top_network]
    ]

    # === Styled table ===
    summary_table = Table(summary_data, hAlign='CENTER', colWidths=[150, 300])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor("#f5f5f5")),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BOX', (0, 0), (-1, -1), 0, HexColor("#f5f5f5")),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 25))


    # Charts (MATPLOTLIB ONLY)
    if include_charts:
        
        add_centered_section_title(story, "Top 10 Countries by Network Count")
        try:
            story.append(matplotlib_bar_chart(top_country_networks_df.head(10)))
        except Exception as e:
            story.append(Paragraph(f"Failed to render bar chart: {e}", styles["Normal"]))
        story.append(Spacer(1, 20))

        add_centered_section_title(story, "Top 10 Networks by Station Count")
        try:
            story.append(matplotlib_pie_chart(top_country_networks_df.head(10)))
        except Exception as e:
            story.append(Paragraph(f"Failed to render pie chart: {e}", styles["Normal"]))
        story.append(Spacer(1, 20))

    # === Map Section (Matplotlib Static Map) ===
    if include_map:
        add_centered_section_title(story, "World Map of Bike Stations")
        try:
            story.append(render_static_world_map(df))  # df must include lat/lon
        except Exception as e:
            story.append(Paragraph(f"Failed to render map: {e}", styles["Normal"]))
        story.append(Spacer(1, 20))

    # Footer
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} by City Bike Network Dashboard.",
        styles["Normal"]
    ))

    doc.build(story)
    return "final_report.pdf"


def render_static_world_map(df, width=400, height=250):
    try:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.scatter(df["longitude"], df["latitude"], s=10, alpha=0.5, c='red')
        ax.set_title("Global Bike Station Distribution")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.grid(True)
        plt.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        plt.close(fig)
        return Image(buf, width=width, height=height)
    except Exception as e:
        return Paragraph(f" Could not render map: {e}", getSampleStyleSheet()["Normal"])


def add_centered_section_title(story, title_text):
    # Heading text, centered and bold
    section_title_style = ParagraphStyle(
        name="SectionTitle",
        fontSize=12,
        leading=14,
        alignment=1,  # Center align
        textColor=colors.HexColor("#111111"),
        fontName="Helvetica-Bold",
        spaceAfter=6
    )
    
    story.append(Paragraph(title_text, style=section_title_style))

    # Gray underline
    story.append(HRFlowable(
        width="80%", 
        thickness=0.5, 
        lineCap='round', 
        color=colors.HexColor("#cccccc"), 
        spaceBefore=1, 
        spaceAfter=12,
        hAlign='CENTER'
    ))
