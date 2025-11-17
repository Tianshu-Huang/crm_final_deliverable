import streamlit as st
from main_dashboard import render_main_dashboard
from ransom_model import render_decision_model_tab  # import the new tab renderer
from scenario_phishing import render_phishing_scenario_tab



def main():
    st.set_page_config(page_title="AHN Ransomware Risk Dashboard", layout="wide")

    # Top-level tab switcher
    tab = st.radio(
    "Select Dashboard:",
    [
        "📊 Risk Simulator",
        "💸 Ransom vs. Recovery",
        "🎣 Phishing Attack Scenario"
    ],
    horizontal=True,
)

    st.divider()

    # Reset sidebar when switching tabs
    if "last_tab" not in st.session_state or st.session_state.last_tab != tab:
        # remove all sidebar keys
        for key in list(st.session_state.keys()):
            if key.startswith("sidebar_"):
                del st.session_state[key]
        st.session_state.last_tab = tab

    # Render active tab
    if tab == "📊 Risk Simulator":
        render_main_dashboard()
    elif tab == "🎣 Phishing Attack Scenario":
        render_phishing_scenario_tab()
    else:
        render_decision_model_tab()


if __name__ == "__main__":
    main()
