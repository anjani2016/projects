import streamlit as st
import folium
from folium.plugins import Geocoder, MiniMap
from streamlit_folium import st_folium
import sys
import os

# Ensure the project root is on the path for data imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.ontario_lakes import ONTARIO_LAKES, get_trophic_color

# ── Page Header ──────────────────────────────────────────────────────────────
st.title("🗺️ Ontario Lake Selector")
st.markdown(
    "Click any lake marker to select it for analysis. "
    "The **Dashboard**, **Risk Model**, and **Field Entry** pages will all update to reflect the selected lake."
)

# ── Legend ───────────────────────────────────────────────────────────────────
col_leg1, col_leg2, col_leg3, col_leg4 = st.columns(4)
col_leg1.markdown("🔵 **Oligotrophic** — Clear, low-nutrient")
col_leg2.markdown("🟢 **Mesotrophic** — Moderate nutrients")
col_leg3.markdown("🔴 **Eutrophic** — High nutrients / Bloom risk")
col_leg4.markdown("📍 **Click a marker** to select a lake")

st.markdown("---")

# ── Build Folium Map ─────────────────────────────────────────────────────────
m = folium.Map(
    location=[44.6, -79.0],
    zoom_start=8,
    tiles="CartoDB positron",
    prefer_canvas=True
)

# Add minimap
MiniMap(toggle_display=True, position="bottomleft").add_to(m)

# Add search box
Geocoder(position="topright").add_to(m)

# Plot each lake as a clickable marker
for lake in ONTARIO_LAKES:
    color = get_trophic_color(lake["trophic_state"])

    popup_html = f"""
    <div style="font-family: sans-serif; min-width: 200px;">
        <h4 style="margin:0 0 6px 0; color:#1a1a2e;">{lake['name']}</h4>
        <table style="font-size:12px; border-collapse:collapse; width:100%">
            <tr><td><b>Trophic State</b></td><td>{lake['trophic_state']}</td></tr>
            <tr><td><b>Area</b></td><td>{lake['area_km2']} km²</td></tr>
            <tr><td><b>Max Depth</b></td><td>{lake['max_depth_m']} m</td></tr>
            <tr><td><b>Baseline TP</b></td><td>{lake['tp_baseline']:.3f} mg/L</td></tr>
            <tr><td><b>Region</b></td><td>{lake['region']}</td></tr>
            <tr><td><b>Conservation Authority</b></td><td>{lake['conservation_authority']}</td></tr>
        </table>
        <p style="font-size:11px;color:#666;margin-top:6px;font-style:italic;">{lake['notes']}</p>
        <p style="font-size:11px;color:#333;margin-top:4px;">
            ✅ <b>Click the marker</b>, then press <b>"Select This Lake"</b> below the map.
        </p>
    </div>
    """

    folium.CircleMarker(
        location=[lake["lat"], lake["lon"]],
        radius=max(8, lake["area_km2"] ** 0.35),   # scale marker by lake area
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7,
        popup=folium.Popup(popup_html, max_width=280),
        tooltip=f"<b>{lake['name']}</b> — {lake['trophic_state']}",
    ).add_to(m)

# ── Render Map ───────────────────────────────────────────────────────────────
map_output = st_folium(m, height=520, width="100%", returned_objects=["last_object_clicked_popup"])

# ── Lake Selection Logic ─────────────────────────────────────────────────────
st.markdown("---")

# Parse which lake was clicked from the popup HTML
clicked_name = None
if map_output and map_output.get("last_object_clicked_popup"):
    popup_text = map_output["last_object_clicked_popup"]
    for lake in ONTARIO_LAKES:
        if lake["name"] in popup_text:
            clicked_name = lake["name"]
            break

# Dropdown as a fallback / manual override
lake_names = [l["name"] for l in ONTARIO_LAKES]
current_selection = st.session_state.get("selected_lake_name", lake_names[0])

# If map was clicked, pre-select that lake in the dropdown
default_idx = lake_names.index(clicked_name) if clicked_name and clicked_name in lake_names else lake_names.index(current_selection) if current_selection in lake_names else 0

col_sel, col_btn = st.columns([3, 1])
with col_sel:
    chosen = st.selectbox(
        "Confirm lake selection (or choose from list):",
        options=lake_names,
        index=default_idx,
        key="lake_selectbox"
    )
with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("✅ Select This Lake", type="primary", use_container_width=True):
        # Find the full lake dict
        for lake in ONTARIO_LAKES:
            if lake["name"] == chosen:
                st.session_state["selected_lake_name"] = lake["name"]
                st.session_state["selected_lake"] = lake
                # Pre-populate dashboard session state with lake-specific baselines
                st.session_state["tp"] = lake["tp_baseline"]
                break
        st.success(f"✅ **{chosen}** selected! Navigate to the Dashboard to begin analysis.")
        st.balloons()

# ── Current Selection Banner ─────────────────────────────────────────────────
if st.session_state.get("selected_lake"):
    lake = st.session_state["selected_lake"]
    trophic_colors = {"Oligotrophic": "blue", "Mesotrophic": "green", "Eutrophic": "red"}
    color = trophic_colors.get(lake["trophic_state"], "gray")

    st.markdown("---")
    st.subheader("📋 Currently Selected Lake")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Lake", lake["name"])
    c2.metric("Trophic State", lake["trophic_state"])
    c3.metric("Baseline TP", f"{lake['tp_baseline']:.3f} mg/L")
    c4.metric("Max Depth", f"{lake['max_depth_m']} m")

    st.markdown(f"**Conservation Authority:** {lake['conservation_authority']}  |  **Region:** {lake['region']}")
    st.info(f"📌 {lake['notes']}")
    st.caption("Navigate to the **Main Dashboard** or **Predictive Risk Model** to run the analysis for this lake.")
else:
    st.info("No lake selected yet. Click a marker on the map, then press **Select This Lake**.")
