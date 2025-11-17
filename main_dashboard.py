import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from pathlib import Path


# ---------- Load CSV-driven simulation parameters ----------
def load_simulation_inputs(path="data/simulation_inputs.csv"):
    p = Path(path)
    if not p.exists():
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



# ---------- MAIN DASHBOARD ----------
def render_main_dashboard():
    st.title("AHN Ransomware Risk Dashboard")

    # ---- Load CSV parameters ----
    params = load_simulation_inputs()

    # ---- SIDEBAR (unchanged user controls) ----
    st.sidebar.header("Control Settings")
    mfa = st.sidebar.slider("MFA Coverage (%)", 0, 100, int(params["Default_MFA"]))
    edr = st.sidebar.slider("EDR Deployment (%)", 0, 100, int(params["Default_EDR"]))
    soc = st.sidebar.slider("SOC Coverage (hours/day)", 8, 24, int(params["Default_SOC"]))
    backup = st.sidebar.slider("Backup Strength (RTO hours)", 1, 48, int(params["Default_Backup"]))
    budget = st.sidebar.number_input(
        "Security Investment ($M)", 0.0, 100.0, float(params["Default_Budget"])
    )

    # ---- Base Monte Carlo Parameters (from CSV) ----
    base_freq = float(params["Base_Frequency"])
    base_loss_mu = float(params["Base_Loss_Mu"])
    base_loss_sigma = float(params["Base_Loss_Sigma"])
    baseline_cost = float(params["Baseline_Cost"])  # used only for display

    N = 10000  # Monte Carlo iterations

    # ============================================================
    # 🚨 BASELINE SCENARIO = NO CONTROLS (for ROI calculations)
    # ============================================================

    # No-control settings
    base_mfa = 0
    base_edr = 0
    base_soc = 8
    base_backup = 48

    # Frequency and loss modifiers for "no controls"
    freq_modifier_base = (1 - (base_mfa / 100) * 0.5) * (1 - (base_soc - 8) / 16 * 0.2)
    loss_modifier_base = (1 - (base_edr / 100) * 0.4) * (1 - (base_backup / 48) * 0.3)

    # Adjusted parameters (baseline)
    adjusted_freq_base = base_freq * freq_modifier_base
    adjusted_mu_base = base_loss_mu - np.log(loss_modifier_base + 1e-6)

    # Baseline Monte Carlo
    losses_base = np.random.lognormal(adjusted_mu_base, base_loss_sigma, N)
    annual_losses_base = losses_base * adjusted_freq_base
    EAL_baseline = np.mean(annual_losses_base)

    # ============================================================
    # 🚨 CURRENT SCENARIO (with user-selected controls)
    # ============================================================

    freq_modifier = (
    (1 - (mfa / 100) * 0.45) *
    (1 - (edr / 100) * 0.15) *
    (1 - ((soc - 8) / 16) * 0.25)
    )
    freq_modifier = max(0.05, freq_modifier)

    loss_modifier = (
    (1 - (edr / 100) * 0.35) *
    (1 - ((soc - 8) / 16) * 0.20) *
    (1 - (backup / 48) * 0.50)
    )
    loss_modifier = max(0.05, loss_modifier)


    adjusted_freq = base_freq * freq_modifier
    adjusted_mu = base_loss_mu - np.log(loss_modifier + 1e-6)

    losses = np.random.lognormal(adjusted_mu, base_loss_sigma, N)
    annual_losses = losses * adjusted_freq

    EAL = np.mean(annual_losses)
    P95 = np.percentile(annual_losses, 95)
    std_dev = np.std(annual_losses)

    # ============================================================
    # 🟩 NEW ROI = (Baseline EAL − Current EAL) / Budget
    # ============================================================
    roi_val = (EAL_baseline - EAL) / (budget * 1_000_000)

    # ============================================================
    # ⭐ RESTORED ORIGINAL LAYOUT: TOP METRICS
    # ============================================================
    st.subheader("Simulation Results")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Baseline EAL (No Controls)", f"${EAL_baseline/1e6:.2f}M")
    c2.metric("EAL With Controls", f"${EAL/1e6:.2f}M")
    c3.metric("95th Percentile Loss", f"${P95/1e6:.2f}M")
    c4.metric("ROI (Risk Reduction)", f"{roi_val:.2f}x")

    # ============================================================
    # 📊 LOSS DISTRIBUTION HISTOGRAM
    # ============================================================
    fig = px.histogram(
        annual_losses / 1e6,
        nbins=40,
        title="Loss Distribution (Millions USD)",
        labels={"value": "Simulated Annual Loss (M USD)"}
    )
    st.plotly_chart(fig, use_container_width=True)

    # ============================================================
    # 🔧 CONTROL MODIFIER TABLE
    # ============================================================
    st.markdown("### Control-Based Modifiers")
    modifier_df = pd.DataFrame({
        "Modifier": ["Frequency Modifier", "Loss Modifier", "Adjusted Frequency", "Adjusted Mu"],
        "Value": [freq_modifier, loss_modifier, adjusted_freq, adjusted_mu],
    })
    st.table(modifier_df)

    # ============================================================
    # ⚙️ ADVANCED SETTINGS (COLLAPSIBLE)
    # ============================================================
    with st.expander("⚙️ Advanced Monte Carlo Parameters (Editable)"):
        st.markdown("These base parameters come from simulation_inputs.csv.")

        base_df = pd.DataFrame({
            "Parameter": ["Base Frequency", "Base Loss Mu", "Base Loss Sigma", "Baseline Cost"],
            "Value": [base_freq, base_loss_mu, base_loss_sigma, baseline_cost],
        })

        edited_df = st.data_editor(base_df, use_container_width=True)

        # Update values (if the user edits them)
        base_freq = float(edited_df.loc[0, "Value"])
        base_loss_mu = float(edited_df.loc[1, "Value"])
        base_loss_sigma = float(edited_df.loc[2, "Value"])
        baseline_cost = float(edited_df.loc[3, "Value"])

    # ============================================================
    # 📋 MONTE CARLO SUMMARY TABLE
    # ============================================================
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

    st.caption("Monte Carlo model compares baseline EAL (no controls) vs. current control posture to compute ROI.")

