import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

# --- 1. UI Input Section ---
st.title("AHN Ransomware Risk Dashboard")

st.sidebar.header("Control Settings")
mfa = st.sidebar.slider("MFA Coverage (%)", 0, 100, 70)
edr = st.sidebar.slider("EDR Deployment (%)", 0, 100, 60)
soc = st.sidebar.slider("SOC Coverage (hours/day)", 8, 24, 16)
backup = st.sidebar.slider("Backup Strength (RTO hours)", 1, 48, 12)
budget = st.sidebar.number_input("Security Investment ($M)", 0.0, 100.0, 3.0)

# --- 2. Simulation Parameters ---
N = 10000  # number of Monte Carlo iterations
base_freq = 1.0  # expected ransomware incidents/year
base_loss_mu, base_loss_sigma = 14, 1.0  # lognormal params (~$1.2M median)
baseline_cost = 3_000_000  # baseline annual loss (example)

# --- 3. Apply Control Effectiveness (simple modifiers) ---
freq_modifier = (1 - (mfa / 100) * 0.5) * (1 - (soc - 8)/16 * 0.2)
loss_modifier = (1 - (edr / 100) * 0.4) * (1 - (backup/48) * 0.3)

adjusted_freq = base_freq * freq_modifier
adjusted_mu = base_loss_mu - np.log(loss_modifier + 1e-6)

# --- 4. Monte Carlo Simulation ---
losses = np.random.lognormal(adjusted_mu, base_loss_sigma, N)
annual_losses = losses * adjusted_freq
EAL = np.mean(annual_losses)
P95 = np.percentile(annual_losses, 95)

# --- 5. Visualization ---
st.subheader("Simulation Results")
st.metric("Expected Annual Loss (EAL)", f"${EAL/1e6:.2f} M")
st.metric("95th Percentile Loss", f"${P95/1e6:.2f} M")
st.metric("Estimated Downtime", f"{backup:.1f} hrs (RTO target)")
st.metric("ROI Estimate", f"{(baseline_cost - EAL)/budget:.1f}x")

fig = px.histogram(annual_losses/1e6, nbins=40,
                   title="Loss Distribution (Millions USD)",
                   labels={"value": "Simulated Annual Loss"})
st.plotly_chart(fig, use_container_width=True)
