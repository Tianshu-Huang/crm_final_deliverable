import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from pathlib import Path

"""
Phishing Scenario Model Notes & Data Sources
----------------------------------------------

This file models the phishing -> credential theft -> ransomware encryption path.
Basically the "classic" healthcare ransomware entry point.

'm putting all the key parameters here so it's clear where everything came from:

Phishing attack volume:
    Comes from the AHN stats sheet.
    There were ~6428 attacks/month, and about 80% of them are phishing,
    so roughly ~5000 phishing attempts per month.

Email hit rate (what gets past filters):
    This is not directly in the dataset, so we used 2%, which is pretty normal
    for healthcare environments.

Click rate:
    Most studies say 2-8% for hospitals. We picked 5% as a middle ground assumption.

Credential compromise probability:
    Assumed 20% of malicious clicks lead to a compromised account.
    This is from industry averages, not AHN specific.

Detection time (MTTD):
    This is estimated form past AHN attacks.
    It usually takes 30-60 days for AHN to detect a ransomware that's been sitting in its env.

Recovery time (MTTR):
    48 hours is pretty typical for ransomware restoration in hospitals.

Downtime cost per hour:
    Estimated to be $75k/hr

Controls:
    MFA reduces frequency (prevents reuse of stolen credentials).
    EDR reduces severity (stops malware execution/lateral movement).
    SOC affects detection speed affects frequency.
    Backup RTO affects severity directly (longer restore -> higher cost).
    All starting values in controls are estimated.

CSV:
    data/phishing_params.csv

Data sources behind the scenes:
    - A bunch of numbers are directly from the AHN sheets,
    - Some are industry-standard healthcare numbers,
    - And some pieces (click rate, compromise probability) are assumptions.

"""


# -------------------------------------------------------------------
# Load CSV Parameters
# -------------------------------------------------------------------
def load_phishing_inputs(path="data/phishing_scenario_inputs.csv"):
    """
    Load phishing scenario baseline parameters from CSV.

    Returns fallback defaults if the file is missing.
    """
    p = Path(path)
    if not p.exists():
        st.warning(f"{path} not found. Using fallback defaults.")
        return {
            "Phishing_Rate": 0.35,
            "Training_Effectiveness": 0.40,
            "MFA_Strength": 0.60,
            "Credential_Dumping_Prob": 0.50,
            "Lateral_Movement_Prob": 0.40,
            "EHR_Encryption_Prob": 0.70,
            "Avg_Cost_Per_Hour": 75000.0,
            "Downtime_Hours": 24.0,
        }

    df = pd.read_csv(p)
    return {row["Parameter"]: row["Value"] for _, row in df.iterrows()}


# -------------------------------------------------------------------
# Scenario Probability / Loss Calculation
# -------------------------------------------------------------------
def compute_phishing_scenario(
    phishing_rate,
    training_effectiveness,
    mfa_strength,
    credential_dumping_prob,
    lateral_movement_prob,
    ehr_encryption_prob,
    avg_cost_per_hour,
    downtime_hours,
):
    """
    Execute the phishing → credential theft → lateral movement → encryption
    probability chain and compute expected financial loss.
    """

    # Probability that a phishing attempt results in a user click
    click_probability = phishing_rate * (1 - training_effectiveness)

    # Probability an account is compromised after a click
    credential_compromise = (
        click_probability * credential_dumping_prob * (1 - mfa_strength)
    )

    # Probability attacker moves laterally from that account
    lateral_success = credential_compromise * lateral_movement_prob

    # Probability EHR encryption occurs after lateral movement
    final_ehr_attack_prob = lateral_success * ehr_encryption_prob

    # Expected financial loss = attack probability × downtime × cost/hr
    expected_loss = final_ehr_attack_prob * downtime_hours * avg_cost_per_hour

    return {
        "Click Probability": click_probability,
        "Credential Compromise Probability": credential_compromise,
        "Lateral Movement Probability": lateral_success,
        "EHR Encryption Probability": final_ehr_attack_prob,
        "Expected Loss (USD)": expected_loss,
    }


# -------------------------------------------------------------------
# Main Phishing Scenario Dashboard Tab
# -------------------------------------------------------------------
def render_phishing_scenario_tab():
    """Render the phishing → credential compromise → encryption scenario dashboard."""
    st.title("🎣 Phishing -> Credential Compromise -> EHR Encryption Scenario")

    st.write("""
    This dashboard models a realistic MITRE ATT&CK ransomware chain common in healthcare:

    **Phishing -> Credential Harvesting -> Lateral Movement -> EHR Encryption**
    
    Based on ATT&CK Techniques:
    - T1566 Phishing  
    - T1003 Credential Dumping  
    - T1078 Valid Accounts  
    - T1021 Lateral Movement (Remote Services)  
    - T1486 Data Encrypted for Impact  
    """)

    # ------------------- Load CSV defaults -------------------
    inputs = load_phishing_inputs()

    # ------------------- Sidebar Inputs -------------------
    st.sidebar.header("⚙️ Scenario Inputs (CSV-Driven Defaults)")

    phishing_rate = st.sidebar.slider(
        "Phishing Email Hit Rate",
        0.0, 1.0,
        float(inputs["Phishing_Rate"]),
        step=0.01,
        key="phish_rate"
    )

    training_effectiveness = st.sidebar.slider(
        "Training Effectiveness",
        0.0, 1.0,
        float(inputs["Training_Effectiveness"]),
        step=0.05,
        key="phish_training"
    )

    mfa_strength = st.sidebar.slider(
        "MFA Coverage Effectiveness",
        0.0, 1.0,
        float(inputs["MFA_Strength"]),
        step=0.05,
        key="phish_mfa"
    )

    credential_dumping_prob = st.sidebar.slider(
        "Credential Dumping Success Probability",
        0.0, 1.0,
        float(inputs["Credential_Dumping_Prob"]),
        step=0.05,
        key="phish_creddump"
    )

    lateral_movement_prob = st.sidebar.slider(
        "Lateral Movement Success Probability",
        0.0, 1.0,
        float(inputs["Lateral_Movement_Prob"]),
        step=0.05,
        key="phish_lateral"
    )

    ehr_encryption_prob = st.sidebar.slider(
        "EHR Encryption Probability",
        0.0, 1.0,
        float(inputs["EHR_Encryption_Prob"]),
        step=0.05,
        key="phish_encrypt"
    )

    avg_cost_per_hour = st.sidebar.number_input(
        "Downtime Cost per Hour (USD)",
        0.0, 5_000_000.0,
        float(inputs["Avg_Cost_Per_Hour"]),
        step=5000.0,
        key="phish_cost_hour"
    )

    downtime_hours = st.sidebar.number_input(
        "Estimated EHR Downtime (Hours)",
        0.0, 240.0,
        float(inputs["Downtime_Hours"]),
        step=1.0,
        key="phish_downtime"
    )

    # ------------------- Run Scenario -------------------
    results = compute_phishing_scenario(
        phishing_rate,
        training_effectiveness,
        mfa_strength,
        credential_dumping_prob,
        lateral_movement_prob,
        ehr_encryption_prob,
        avg_cost_per_hour,
        downtime_hours,
    )

    # ------------------- Display Metrics -------------------
    st.subheader("Scenario Risk Metrics")

    c1, c2, c3 = st.columns(3)
    c1.metric("Credential Compromise", f"{results['Credential Compromise Probability']*100:.2f}%")
    c2.metric("Lateral Movement Success", f"{results['Lateral Movement Probability']*100:.2f}%")
    c3.metric("EHR Encryption Likelihood", f"{results['EHR Encryption Probability']*100:.2f}%")

    st.metric("Expected Financial Loss", f"${results['Expected Loss (USD)']:,.0f}")

    # ------------------- Detailed Results Table -------------------
    st.markdown("### Detailed Scenario Table")

    df = pd.DataFrame({
        "Metric": list(results.keys()),
        "Value": list(results.values())
    })
    st.dataframe(df, use_container_width=True)

    # ------------------- Funnel Visualization -------------------
    st.markdown("### Attack Chain Probability Funnel")

    funnel_df = pd.DataFrame({
        "Stage": [
            "Phishing Email Sent",
            "User Clicks",
            "Credential Compromise",
            "Lateral Movement",
            "EHR Encryption"
        ],
        "Probability": [
            phishing_rate,
            results["Click Probability"],
            results["Credential Compromise Probability"],
            results["Lateral Movement Probability"],
            results["EHR Encryption Probability"]
        ]
    })

    fig = px.funnel(
        funnel_df,
        x="Probability",
        y="Stage",
        title="MITRE ATT&CK Chain: Probability of Success",
    )

    st.plotly_chart(fig, use_container_width=True)

    st.caption("All scenario inputs are loaded from data/phishing_scenario_inputs.csv and can be tuned without any code changes.")
