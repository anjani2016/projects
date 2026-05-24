# src/core/utils.py
import logging
import streamlit as st
import os
import random

def setup_logger(log_level=logging.INFO):
    """Configures the project-specific logging engine with custom formats, console, and file handlers."""
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] - %(message)s'
    )
    
    # Configure both "src" and "ieso_hedging_tool" namespaces
    for name in ["src", "ieso_hedging_tool"]:
        logger = logging.getLogger(name)
        logger.setLevel(log_level)
        
        # Avoid duplicate handlers if the app reloads (common in Streamlit)
        if not logger.handlers:
            # 1. Console Stream Handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # 2. File Handler to preserve audit logs
            os.makedirs("logs", exist_ok=True)
            file_handler = logging.FileHandler("logs/project_log.txt", encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            # Prevent logs from bubbling up to noisy root loggers
            logger.propagate = False
            
    return logging.getLogger("ieso_hedging_tool")


def initialize_project():
    """Creates the necessary folder structure automatically and initializes logging."""
    folders = [
        'data/raw', 
        'data/processed', 
        'data/assets', 
        'logs'
    ]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
    
    # Initialize the project-wide logger
    logger = setup_logger()
    logger.info("Project directories and logging engine initialized.")

def format_currency(value):
    return f"${value:,.2f}"


def add_sidebar_branding():
    """Restores the logo to the top-left position."""
    logo_path = "data/assets/CR_logo.png"
    if os.path.exists(logo_path):
        st.logo(logo_path, icon_image=logo_path)
    
    # The logo is placed here, navigation will follow automatically

def add_sidebar_footer():
    """Adds philosophical insights to the bottom of the sidebar."""
    insights = [
        "**Mass Balance:** Every $1 spike in HOEP must be recovered by a Δ of 1.0.",
        "**Gravity:** Energy is a physical commodity; it must return to the mean (OU Process).",
        "**Hedge Gap:** The delta between your Strike and Spot is your 'Unfunded Risk'.",
        "**The P.Eng Oath:** Protect the budget from catastrophic price spikes."
    ]
    st.sidebar.divider()
    st.sidebar.caption(f"🚀 **Antigravity Insight:**\n\n{random.choice(insights)}")
    # 2. Contact Info (Placed before navigation links in main.py)
    st.sidebar.markdown("**Contact & Support**")
    c1, c2 = st.sidebar.columns(2)
    with c1:
        st.sidebar.caption("[📧 Email](mailto:anjani@centauri-research.com)")
    with c2:
        st.sidebar.caption("[🌐 Website](https://centauri-research.com/)")
