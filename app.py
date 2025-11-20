import streamlit as st

# Import individual dashboard renderers
from main_dashboard import render_main_dashboard
from ransom_model import render_decision_model_tab
from scenario_phishing import render_phishing_scenario_tab
from scenario_vendor import render_vendor_compromise_tab


def main():
    """
    Entry point for the AHN Ransomware Risk Dashboard.
    Handles page configuration, tab navigation, and state reset behavior.
    """

    # Configure Streamlit page
    st.set_page_config(
        page_title="AHN Ransomware Risk Dashboard",
        layout="wide"
    )

    # --- Top-Level Navigation ---
    # Main tab selector controlling which dashboard to display
    tab = st.radio(
        "Select Dashboard:",
        [
            "Risk Simulator",
            "Ransom vs. Recovery",
            "Phishing Attack Scenario",
            "Vendor Compromise Scenario"
        ],
        horizontal=True,
    )

    st.divider()

    # --- Sidebar Reset Logic ---
    # Reset all sidebar_* session state keys when switching tabs.
    # This ensures that sidebar controls are cleanly refreshed and do not leak
    # values across different dashboard pages.
    if "last_tab" not in st.session_state or st.session_state.last_tab != tab:
        for key in list(st.session_state.keys()):
            if key.startswith("sidebar_"):
                del st.session_state[key]
        st.session_state.last_tab = tab

    # --- Render Dashboard Based on Active Tab ---
    if tab == "Risk Simulator":
        render_main_dashboard()

    elif tab == "Ransom vs. Recovery":
        render_decision_model_tab()

    elif tab == "Phishing Attack Scenario":
        render_phishing_scenario_tab()

    elif tab == "Vendor Compromise Scenario":
        render_vendor_compromise_tab()


# Script entry point
if __name__ == "__main__":
    main()
