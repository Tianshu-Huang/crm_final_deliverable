import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from pathlib import Path


# -----------------------------
# Load Phishing Parameters from CSV
# -----------------------------
def load_phishing_inputs(path="data/phishing_scenario_inputs.csv"):
    p = Path(path)
    if not p.exists():
        st.warning(f"⚠️ {path} not found. Using fallback defaults.")
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


# -----------------------------
# Scenario Calculation
# -----------------------------
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
    click_probability = phishing_rate * (1 - training_effectiveness)

    credential_compromise = click_probability * credential_dumping_prob * (1 - mfa_strength)

    lateral_success = credential_compromise * lateral_movement_prob

    final_ehr_attack_prob = lateral_success * ehr_encryption_prob

    expected_loss = final_ehr_attack_prob * downtime_hours * avg_cost_per_hour

    return {
        "Click Probability": click_probability,
        "Credential Compromise Probability": credential_compromise,
        "Lateral Movement Probability": lateral_success,
        "EHR Encryption Probability": final_ehr_attack_prob,
        "Expected Loss (USD)": expected_loss,
    }


# -----------------------------
# MAIN DASHBOARD TAB
# -----------------------------
def render_phishing_scenario_tab():
    st.title("🎣 Phishing → Credential Compromise → EHR Encryption Scenario")

    st.write("""
    This dashboard models a realistic MITRE ATT&CK ransomware chain common in healthcare:

    **Phishing → Credential Harvesting → Lateral Movement → EHR Encryption**
    
    Based on ATT&CK Techniques:
    - T1566 Phishing  
    - T1003 Credential Dumping  
    - T1078 Valid Accounts  
    - T1021 Lateral Movement (Remote Services)  
    - T1486 Data Encrypted for Impact  
    """)

    # -------------------
    # Load Default Inputs from CSV
    # -------------------
    inputs = load_phishing_inputs()

    # -------------------
    # Sidebar Inputs (CSV-driven)
    # -------------------
    st.sidebar.header("⚙️ Scenario Inputs (CSV-Driven Defaults)")

    phishing_rate = st.sidebar.slider(
        "Phishing Email Hit Rate",
        float(0.0), float(1.0),
        float(inputs["Phishing_Rate"]),
        step=0.01,
        key="phish_rate"
    )

    training_effectiveness = st.sidebar.slider(
        "Training Effectiveness",
        float(0.0), float(1.0),
        float(inputs["Training_Effectiveness"]),
        step=0.05,
        key="phish_training"
    )

    mfa_strength = st.sidebar.slider(
        "MFA Coverage Effectiveness",
        float(0.0), float(1.0),
        float(inputs["MFA_Strength"]),
        step=0.05,
        key="phish_mfa"
    )

    credential_dumping_prob = st.sidebar.slider(
        "Credential Dumping Success Probability",
        float(0.0), float(1.0),
        float(inputs["Credential_Dumping_Prob"]),
        step=0.05,
        key="phish_creddump"
    )

    lateral_movement_prob = st.sidebar.slider(
        "Lateral Movement Success Probability",
        float(0.0), float(1.0),
        float(inputs["Lateral_Movement_Prob"]),
        step=0.05,
        key="phish_lateral"
    )

    ehr_encryption_prob = st.sidebar.slider(
        "EHR Encryption Probability",
        float(0.0), float(1.0),
        float(inputs["EHR_Encryption_Prob"]),
        step=0.05,
        key="phish_encrypt"
    )

    avg_cost_per_hour = st.sidebar.number_input(
        "Downtime Cost per Hour (USD)",
        float(0.0), float(5_000_000.0),
        float(inputs["Avg_Cost_Per_Hour"]),
        step=float(5000.0),
        key="phish_cost_hour"
    )

    downtime_hours = st.sidebar.number_input(
        "Estimated EHR Downtime (Hours)",
        float(0.0), float(240.0),
        float(inputs["Downtime_Hours"]),
        step=float(1.0),
        key="phish_downtime"
    )

    # -------------------
    # Run Scenario Model
    # -------------------
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

    # -------------------
    # Display Results
    # -------------------
    st.subheader("📊 Scenario Risk Metrics")

    c1, c2, c3 = st.columns(3)
    c1.metric("Credential Compromise", f"{results['Credential Compromise Probability']*100:.2f}%")
    c2.metric("Lateral Movement Success", f"{results['Lateral Movement Probability']*100:.2f}%")
    c3.metric("EHR Encryption Likelihood", f"{results['EHR Encryption Probability']*100:.2f}%")

    st.metric("Expected Financial Loss", f"${results['Expected Loss (USD)']:,.0f}")

    # -------------------
    # Table Output
    # -------------------
    st.markdown("### 📋 Detailed Scenario Table")
    df = pd.DataFrame({
        "Metric": list(results.keys()),
        "Value": list(results.values())
    })
    st.dataframe(df, use_container_width=True)

    # -------------------
    # Visualization: Attack Funnel
    # -------------------
    st.markdown("### 📈 Attack Chain Probability Funnel")

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
            results["EHR Encryption Probability"],
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
