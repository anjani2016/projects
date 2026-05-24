from pathlib import Path
import streamlit as st


def apply_branding() -> None:
    # Sidebar typography with icon-font safety so Material icons do not render as text.
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            font-family: "Inter", "Segoe UI", sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: 0.2px;
        }
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] {
            font-family: "Inter", "Segoe UI", sans-serif !important;
            font-weight: 400 !important;
        }
        .material-symbols-rounded,
        .material-symbols-outlined {
            font-family: "Material Symbols Rounded", "Material Symbols Outlined" !important;
            font-weight: normal !important;
            font-style: normal !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Use app-level logo to keep it above Streamlit page navigation.
    logo_candidates = [
        Path("data/assets/centauri-research.png"),
        Path("data/assets/centauri_research.png"),
        Path("data/assets/CR_logo.png"),
    ]
    logo_path = next((p for p in logo_candidates if p.exists()), None)
    if logo_path:
        st.logo(str(logo_path))
