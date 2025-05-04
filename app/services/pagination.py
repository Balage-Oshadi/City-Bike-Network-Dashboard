import plotly.express as px
import streamlit as st



# Custom pagination UI
def render_pagination_ui(current_page: int, total_pages: int, page_key_prefix: str) -> int:
    """
    Renders a custom pagination UI with numbered buttons and navigation arrows.

    Args:
        current_page (int): The current active page.
        total_pages (int): The total number of pages.
        page_key_prefix (str): Unique key prefix to avoid Streamlit key collisions.

    Returns:
        int: The newly selected page number (or current if unchanged).
    """
    max_display_pages = 5
    half_range = max_display_pages // 2

    # Determine visible page range
    start_page = max(current_page - half_range, 1)
    end_page = min(start_page + max_display_pages - 1, total_pages)

    if end_page - start_page < max_display_pages:
        start_page = max(end_page - max_display_pages + 1, 1)

    # Create columns for navigation buttons and page numbers
    total_cols = max_display_pages + 4  # « ‹ page1 page2 ... › »
    cols = st.columns(total_cols)
    col_idx = 0

    # First Page «
    if cols[col_idx].button("«", key=f"{page_key_prefix}_first"):
        return 1
    col_idx += 1

    # Previous Page ‹
    if current_page > 1:
        if cols[col_idx].button("‹", key=f"{page_key_prefix}_prev"):
            return current_page - 1
    col_idx += 1

    # Page Numbers
    for page_num in range(start_page, end_page + 1):
        if page_num == current_page:
            cols[col_idx].markdown(
                f"<div style='background-color:#1976d2; color:white; padding:6px 12px; border-radius:20px; text-align:center; font-weight:bold;'>{page_num}</div>",
                unsafe_allow_html=True
            )
        else:
            if cols[col_idx].button(f"{page_num}", key=f"{page_key_prefix}_p_{page_num}"):
                return page_num
        col_idx += 1

    # Next Page ›
    if current_page < total_pages:
        if cols[col_idx].button("›", key=f"{page_key_prefix}_next"):
            return current_page + 1
    col_idx += 1

    # Last Page »
    if cols[col_idx].button("»", key=f"{page_key_prefix}_last"):
        return total_pages

    return current_page


