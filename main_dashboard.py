import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from pathlib import Path

"""
General Ransomware Risk Simulator Notes & Data Sources
------------------------------------------------------

This is the overall ransomware model tab. It's meant to be a generic,
high-level risk simulator rather than tied to a specific attack chain.
The idea is that this tab gives leadership a high-level EAL estimate, while the
other tabs go into detailed scenarios.

Here's where the data comes from:

Base_Frequency:
    This is roughly derived from AHN's historical breach rate combined with
    general US healthcare ransomware frequency, but we let the CSV override.

Base_Loss_Mu / Base_Loss_Sigma:
    Also from the CSV. These are the lognormal parameters before controls.
    We tuned them so that the raw (uncontrolled) distribution roughly matches
    healthcare ransomware losses (multi-million-dollar typical events).

Baseline_Cost:
    Only used for ROI display. This is whatever the CSV contains. Not a real
    cost, just a reference point.

Controls:
    MFA reduces frequency.
    EDR reduces severity.
    SOC coverage reduces dwell time (frequency only).
    Backup RTO ncreases severity (longer restore = more damage).
    Budget only relevant for ROI.
    All starting values in controls are estimated.

CSV:
    data/simulation_inputs.csv

Data sources behind the scenes:
    - AHN ransomware stats sheet (for frequency)
    - Healthcare downtime cost ($75k/hr) from Costs sheet
    - Industry averages for MFA/EDR/SOC effectiveness
    - Some assumptions where the data isn't availables

"""

# -------------------------------------------------------------------
# Load simulation inputs from CSV
# -------------------------------------------------------------------
def load_simulation_inputs(path="data/simulation_inputs.csv"):
    """
    Load baseline ransomware parameters and default control values from CSV.

    Parameters:
        path (str): Path to simulation_inputs.csv

    Returns:
        dict: {Parameter: Value} mapping
    """
    p = Path(path)
    if not p.exists():
        # If CSV missing, fall back to compiled defaults
        st.warning(f"⚠️ Could not find {path}. Using fallback defaults.")
        return {
            "Base_Frequency": 1.0,
            "Base_Loss_Mu": 14.0,
            "Base_Loss_Sigma": 1.0,
            "Baseline_Cost": 3_000_000,
            "Default_MFA": 70,
            "Default_EDR": 60,
            "Default_SOC": 16,
            "Default_Backup": 12,
            "Default_Budget": 3.0,
        }

    df = pd.read_csv(p)
    return {row["Parameter"]: row["Value"] for _, row in df.iterrows()}


# -------------------------------------------------------------------
# Main Dashboard Renderer
# -------------------------------------------------------------------
def render_main_dashboard():
    """
    Render the primary ransomware Monte Carlo simulation dashboard.
    This provides baseline EAL, EAL with controls, loss distribution,
    modifiers table, and ROI calculations.
    """

    st.title("AHN Ransomware Risk Dashboard")

    # -----------------------------------------
    # Load model parameters from CSV
    # -----------------------------------------
    params = load_simulation_inputs()

    # -----------------------------------------
    # Sidebar: User-adjustable controls
    # -----------------------------------------
    st.sidebar.header("⚙️ Control Settings")

    mfa = st.sidebar.slider(
        "MFA Coverage (%)", 0, 100, int(params["Default_MFA"])
    )
    edr = st.sidebar.slider(
        "EDR Deployment (%)", 0, 100, int(params["Default_EDR"])
    )
    soc = st.sidebar.slider(
        "SOC Coverage (hours/day)", 8, 24, int(params["Default_SOC"])
    )
    backup = st.sidebar.slider(
        "Backup Strength (RTO hours)", 1, 48, int(params["Default_Backup"])
    )
    budget = st.sidebar.number_input(
        "Security Investment ($M)", 0.0, 100.0, float(params["Default_Budget"])
    )

    # -----------------------------------------
    # Extract Monte Carlo parameters
    # -----------------------------------------
    base_freq = float(params["Base_Frequency"])
    base_loss_mu = float(params["Base_Loss_Mu"])
    base_loss_sigma = float(params["Base_Loss_Sigma"])
    baseline_cost = float(params["Baseline_Cost"])

    N = 10000  # Monte Carlo iterations

    # -------------------------------------------------------------------
    # BASELINE CASE (Zero Control Posture)
    # -------------------------------------------------------------------

    # Frequency adjustment for "no controls" scenario
    freq_modifier_base = (
        (1 - (0 / 100) * 0.45) *          # MFA = 0%
        (1 - (0 / 100) * 0.15) *          # EDR = 0%
        (1 - ((8 - 8) / 16) * 0.25)       # SOC = 8 hours baseline
    )

    severity_multiplier_base = 1.0  # No severity reduction
    adjusted_freq_base = base_freq * freq_modifier_base

    # Baseline Monte Carlo simulation
    raw_losses_base = np.random.lognormal(base_loss_mu, base_loss_sigma, N)
    annual_losses_base = raw_losses_base * severity_multiplier_base * adjusted_freq_base
    EAL_baseline = np.mean(annual_losses_base)

    # -------------------------------------------------------------------
    # CONTROL MODIFIERS (User-selected)
    # -------------------------------------------------------------------

    # --- Frequency modifiers ---
    freq_modifier = (
        (1 - (mfa / 100) * 0.45) *                # MFA reduces frequency
        (1 - (edr / 100) * 0.15) *                # EDR reduces frequency (not severity)
        (1 - ((soc - 8) / 16) * 0.25)             # SOC reduces frequency via dwell time
    )
    freq_modifier = max(0.05, freq_modifier)      # Prevent unrealistic low frequency
    adjusted_freq = base_freq * freq_modifier

    # --- Severity modifiers ---
    sev_edr = 1 - (edr / 100) * 0.35              # EDR reduces severity
    sev_backup = 1 + (backup / 48) * 0.50         # Longer restores → higher impact

    # Final loss severity multiplier
    loss_modifier = max(0.05, sev_edr * sev_backup)

    # -------------------------------------------------------------------
    # MONTE CARLO SIMULATION WITH CONTROLS
    # -------------------------------------------------------------------
    raw_losses = np.random.lognormal(base_loss_mu, base_loss_sigma, N)
    annual_losses = raw_losses * loss_modifier * adjusted_freq

    # Metrics
    EAL = np.mean(annual_losses)
    P95 = np.percentile(annual_losses, 95)
    std_dev = np.std(annual_losses)

    # ROI metric
    roi_val = (EAL_baseline - EAL) / (budget * 1_000_000)

    # -------------------------------------------------------------------
    # OUTPUT: Summary Metrics
    # -------------------------------------------------------------------
    st.subheader("Simulation Results")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Baseline EAL (No Controls)", f"${EAL_baseline/1e6:.2f}M")
    c2.metric("EAL With Controls", f"${EAL/1e6:.2f}M")
    c3.metric("95th Percentile Loss", f"${P95/1e6:.2f}M")
    c4.metric("ROI (Risk Reduction)", f"{roi_val:.2f}x")

    # -------------------------------------------------------------------
    # Loss distribution histogram
    # -------------------------------------------------------------------
    fig = px.histogram(
        annual_losses / 1e6,
        nbins=40,
        title="Loss Distribution (Millions USD)",
        labels={"value": "Simulated Annual Loss (M USD)"}
    )
    st.plotly_chart(fig, use_container_width=True)

    # -------------------------------------------------------------------
    # Control modifiers table
    # -------------------------------------------------------------------
    st.markdown("### Control-Based Modifiers")
    modifier_df = pd.DataFrame({
        "Modifier": [
            "Frequency Modifier",
            "Severity Multiplier",
            "Adjusted Frequency (events/yr)"
        ],
        "Value": [
            freq_modifier,
            loss_modifier,
            adjusted_freq
        ],
    })
    st.table(modifier_df)

    # -------------------------------------------------------------------
    # Advanced parameter editor (from CSV)
    # -------------------------------------------------------------------
    with st.expander("⚙️ Advanced Monte Carlo Parameters (Editable)"):
        st.markdown("These base parameters come from simulation_inputs.csv.")

        base_df = pd.DataFrame({
            "Parameter": [
                "Base Frequency",
                "Base Loss Mu",
                "Base Loss Sigma",
                "Baseline Cost"
            ],
            "Value": [
                base_freq,
                base_loss_mu,
                base_loss_sigma,
                baseline_cost
            ],
        })

        edited_df = st.data_editor(base_df, use_container_width=True)

        # Update variables with edited values (logic unchanged)
        base_freq = float(edited_df.loc[0, "Value"])
        base_loss_mu = float(edited_df.loc[1, "Value"])
        base_loss_sigma = float(edited_df.loc[2, "Value"])
        baseline_cost = float(edited_df.loc[3, "Value"])

    # -------------------------------------------------------------------
    # Summary table
    # -------------------------------------------------------------------
    st.markdown("### Monte Carlo Summary Table")
    summary_df = pd.DataFrame({
        "Metric": [
            "Baseline EAL (No Controls)",
            "EAL with Controls",
            "95th Percentile Loss",
            "Std Dev of Annual Loss",
            "Adjusted Frequency (events/year)",
            "Baseline Cost (CSV)",
            "ROI (Risk Reduction / Budget)"
        ],
        "Value": [
            f"${EAL_baseline:,.0f}",
            f"${EAL:,.0f}",
            f"${P95:,.0f}",
            f"${std_dev:,.0f}",
            f"{adjusted_freq:.3f}",
            f"${baseline_cost:,.0f}",
            f"{roi_val:.2f}x",
        ]
    })

    st.dataframe(summary_df, use_container_width=True)

    st.caption(
        "Monte Carlo model compares baseline EAL (no controls) vs. current control posture to compute ROI."
    )
