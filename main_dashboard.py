import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px

def render_main_dashboard():
    st.title("📊 AHN Ransomware Risk Dashboard")

    # Sidebar (contextual)
    st.sidebar.header("⚙️ Control Settings")
    mfa = st.sidebar.slider("MFA Coverage (%)", 0, 100, 70, key="sidebar_mfa")
    edr = st.sidebar.slider("EDR Deployment (%)", 0, 100, 60, key="sidebar_edr")
    soc = st.sidebar.slider("SOC Coverage (hours/day)", 8, 24, 16, key="sidebar_soc")
    backup = st.sidebar.slider("Backup Strength (RTO hours)", 1, 48, 12, key="sidebar_backup")
    budget = st.sidebar.number_input("Security Investment ($M)", 0.0, 100.0, 3.0, key="sidebar_budget")

    # Simulation parameters
    N = 10000
    base_freq = 1.0
    base_loss_mu, base_loss_sigma = 14, 1.0
    baseline_cost = 3_000_000

    freq_modifier = (1 - (mfa / 100) * 0.5) * (1 - (soc - 8)/16 * 0.2)
    loss_modifier = (1 - (edr / 100) * 0.4) * (1 - (backup/48) * 0.3)

    adjusted_freq = base_freq * freq_modifier
    adjusted_mu = base_loss_mu - np.log(loss_modifier + 1e-6)

    losses = np.random.lognormal(adjusted_mu, base_loss_sigma, N)
    annual_losses = losses * adjusted_freq
    EAL = np.mean(annual_losses)
    P95 = np.percentile(annual_losses, 95)

    # Display results
    st.subheader("📈 Simulation Results")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Expected Annual Loss (EAL)", f"${EAL/1e6:.2f} M")
    c2.metric("95th Percentile Loss", f"${P95/1e6:.2f} M")
    c3.metric("Estimated Downtime", f"{backup:.1f} hrs (RTO target)")
    c4.metric("ROI Estimate", f"{(baseline_cost - EAL)/budget:.1f}x")

    # Histogram visualization
    fig = px.histogram(
        annual_losses / 1e6,
        nbins=40,
        title="Loss Distribution (Millions USD)",
        labels={"value": "Simulated Annual Loss (Millions USD)"},
    )
    st.plotly_chart(fig, use_container_width=True)

    st.caption("All values simulated for academic illustration only — not based on real AHN data.")


