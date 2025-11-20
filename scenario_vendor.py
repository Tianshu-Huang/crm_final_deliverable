import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

"""
Vendor Compromise Scenario Notes & Data Sources
--------------------------------------------------------

This scenario is trying to capture the "vendor gets hacked -> attacker
abuses vendor access -> exfiltrates PHI -> ransomware" situation. This is
the same pattern that hit a lot of US hospitals recently, and AHN's own
history shows that vendor-related breaches are the main problem (3 out of 5).

Where we got all the numbers:

Vendor breach frequency:
    From the AHN ransomware stats sheet. 3 vendor-related breaches in 5 years,
    so we just modeled that as ~0.6 events per year.

PHI per breach:
    Comes from the Costs sheet, ~71k records on average for healthcare.
    We used that as the PHI exposure.

Cost per PHI record:
    $398/record (from the Costs sheet, which cites Veriti's healthcare report).

Exfiltration probability:
    This is an assumption. We model it as a factor affected by DLP. 

MTTD:
    We used ~20 days. Cloud/vendor breaches tend to get caught earlier than
    phishing-based compromises.

MTTR:
    Estimated to be 48 hrs, same as phishing, cloud-based ransomware recoveries 
    are typically around this range.

Downtime cost/hr:
    Estimated to be $75k/hr

Recovery fixed cost:
    ~$600k based on typical IR + forensic cost for medium-sized hospital breaches.

Controls:
    - Vendor Access Hardening lowers frequency (MFA, key rotation, reducing vendor blast-radius).
    - Cloud IAM Restrictions lowers privilege escalation chance.
    - API Logging Coverage affects detection and dwell time.
    - DLP Coverage is the biggest severity reducer because it caps PHI exfil.
    All starting values in controls are estimated.

CSV:
    data/vendor_params.csv

Data sources behind the scenes:
    Some things are definitely assumptions (e.g., how much DLP reduces exfil), but
    we tried to make them realistic based on real cases and MITRE ENGAGE playbooks.

"""


# -------------------------------------------------------------------
# Load Vendor Scenario Parameters
# -------------------------------------------------------------------
def load_vendor_params(path="data/vendor_params.csv"):
    """
    Load vendor attack scenario parameters from CSV.

    Returns empty dict if file missing or parsing fails.
    """
    p = Path(path)
    if not p.exists():
        return {}

    try:
        df = pd.read_csv(p)
        vals = {}

        # Store all parameters in the file as float values
        for col in df.columns:
            vals[col] = float(df[col].iloc[0])

        return vals

    except Exception:
        return {}


# Load once globally
VENDOR = load_vendor_params()


# -------------------------------------------------------------------
# Expected Attack Cost Calculation
# -------------------------------------------------------------------
def expected_vendor_attack_cost(
    vendor_hardening: float,
    iam_strength: float,
    api_logging: float,
    dlp_coverage: float,
    base_vendor_freq: float,
    mttd: float,
    mttr: float,
    downtime_cost_per_hour: float,
    recovery_cost: float,
    phi_records: float,
    phi_cost_per_record: float,
):
    """
    Models a vendor → cloud → PHI exfiltration → ransomware attack chain.

    Total Expected Cost = Adjusted Frequency × Severity

    Severity includes:
    - PHI exfiltration cost
    - Downtime cost
    - Fixed IR recovery cost
    """

    # -------------------- FREQUENCY ADJUSTMENTS --------------------
    freq_modifier = (
        (1 - vendor_hardening * 0.40)     # vendor controls have big impact
        * (1 - iam_strength * 0.25)
        * (1 - api_logging * 0.15)
    )

    adjusted_freq = base_vendor_freq * freq_modifier

    # -------------------- SEVERITY ADJUSTMENTS --------------------
    # DLP reduces PHI records lost
    exfil_success = (1 - dlp_coverage * 0.50)
    phi_breach_cost = phi_records * phi_cost_per_record * exfil_success

    # Downtime cost
    downtime_hours = mttd + mttr
    downtime_cost = downtime_hours * downtime_cost_per_hour

    total_severity = phi_breach_cost + downtime_cost + recovery_cost

    expected_cost = adjusted_freq * total_severity

    return expected_cost, adjusted_freq, total_severity, phi_breach_cost, downtime_cost


# -------------------------------------------------------------------
# Main Vendor Compromise Dashboard Tab
# -------------------------------------------------------------------
def render_vendor_compromise_tab():
    """Render the vendor compromise → cloud abuse → PHI exfiltration scenario dashboard."""
    st.header("Vendor Compromise -> Cloud Abuse -> PHI Exfiltration Scenario")

    st.write("""
        This scenario models a modern supply-chain attack where a **third-party vendor account** is compromised,
        granting attackers access to **AHN cloud APIs**, followed by **PHI exfiltration** and finally encryption
        for monetary extortion ("double extortion" ransomware).
        
        This aligns with AHN's real breach history:
        **3 out of 4 breaches in the past five years** originated from vendor compromise.
    """)

    # ------------------- Load Defaults from CSV -------------------
    base_vendor_freq = VENDOR.get("BaseVendorFrequency", 0.6)
    default_mttd = VENDOR.get("MTTD_hours", 480)
    default_mttr = VENDOR.get("MTTR_hours", 48)
    default_downtime_cost = VENDOR.get("DowntimeCostPerHour", 75000)
    default_recovery_cost = VENDOR.get("RecoveryFixedCost", 600000)
    default_phi_records = VENDOR.get("PHI_Records", 71276)
    default_phi_cost_per_record = VENDOR.get("CostPerRecord", 398)

    # Control defaults
    default_vendor_hardening = VENDOR.get("DefaultVendorHardening", 0.25)
    default_iam_strength = VENDOR.get("DefaultIAMStrength", 0.20)
    default_api_logging = VENDOR.get("DefaultAPILogging", 0.35)
    default_dlp_coverage = VENDOR.get("DefaultDLPCoverage", 0.30)

    # ------------------- Sidebar Controls -------------------
    with st.sidebar:
        st.markdown("### ⚙️ Vendor Scenario Controls")

        vendor_hardening = st.slider(
            "Vendor Access Hardening (%)",
            0.0, 1.0, default_vendor_hardening, step=0.05,
            key="sidebar_vendor_hardening"
        )

        iam_strength = st.slider(
            "Cloud IAM Restriction Strength (%)",
            0.0, 1.0, default_iam_strength, step=0.05,
            key="sidebar_iam_strength"
        )

        api_logging = st.slider(
            "API / Cloud Logging Coverage (%)",
            0.0, 1.0, default_api_logging, step=0.05,
            key="sidebar_api_logging"
        )

        dlp_coverage = st.slider(
            "DLP Coverage (%)",
            0.0, 1.0, default_dlp_coverage, step=0.05,
            key="sidebar_dlp"
        )

        st.markdown("---")

        mttd = st.number_input(
            "MTTD (hours)",
            0.0, 2000.0, default_mttd, step=12.0,
            key="sidebar_mttd_vendor"
        )

        mttr = st.number_input(
            "MTTR (hours)",
            0.0, 500.0, default_mttr, step=4.0,
            key="sidebar_mttr_vendor"
        )

        downtime_cost_per_hour = st.number_input(
            "Downtime Cost per Hour (USD)",
            0.0, 500000.0, default_downtime_cost, step=5000.0,
            key="sidebar_downtime_vendor"
        )

        recovery_cost = st.number_input(
            "Recovery Fixed Cost (USD)",
            0.0, 20000000.0, default_recovery_cost, step=25000.0,
            key="sidebar_recovery_vendor"
        )

        phi_records = st.number_input(
            "PHI Records At Risk",
            0, 500000, int(default_phi_records),
            key="sidebar_phi_records"
        )

        phi_cost_per_record = st.number_input(
            "Cost per PHI Record (USD)",
            0, 1000, int(default_phi_cost_per_record),
            key="sidebar_phi_cost"
        )

    # ------------------- Compute Expected Cost -------------------
    expected_cost, adj_freq, severity, phi_cost, down_cost = expected_vendor_attack_cost(
        vendor_hardening,
        iam_strength,
        api_logging,
        dlp_coverage,
        base_vendor_freq,
        mttd,
        mttr,
        downtime_cost_per_hour,
        recovery_cost,
        phi_records,
        phi_cost_per_record,
    )

    # ------------------- Output Metrics -------------------
    st.subheader("Scenario Results")

    c1, c2, c3 = st.columns(3)
    c1.metric("Annual Frequency", f"{adj_freq:.2f} events/year")
    c2.metric("PHI Breach Cost", f"${phi_cost:,.0f}")
    c3.metric("Total Expected Loss (EAL)", f"${expected_cost:,.0f}")

    st.markdown(f"**Downtime Cost:** ${down_cost:,.0f}")

    # ------------------- Sensitivity: DLP Coverage -------------------
    st.markdown("### Sensitivity: Cost vs DLP Coverage")

    dlp_values = np.linspace(0.0, 1.0, 50)
    dlp_costs = []

    for d in dlp_values:
        c, *_ = expected_vendor_attack_cost(
            vendor_hardening, iam_strength, api_logging, d,
            base_vendor_freq, mttd, mttr, downtime_cost_per_hour,
            recovery_cost, phi_records, phi_cost_per_record
        )
        dlp_costs.append(c)

    fig = px.line(
        x=dlp_values,
        y=dlp_costs,
        labels={"x": "DLP Coverage (%)", "y": "Total Expected Loss (USD)"},
        title="Impact of DLP Coverage on Expected Loss"
    )

    st.plotly_chart(fig, use_container_width=True)

    # ------------------- Heatmap (IAM vs DLP) -------------------
    st.markdown("### Heatmap: IAM Strength vs DLP Coverage")

    iam_vals = np.linspace(0.0, 1.0, 20)
    dlp_vals = np.linspace(0.0, 1.0, 20)

    Z = np.zeros((len(iam_vals), len(dlp_vals)))

    # Compute grid of expected loss values
    for i, iam_ in enumerate(iam_vals):
        for j, dlp_ in enumerate(dlp_vals):
            Z[i, j], *_ = expected_vendor_attack_cost(
                vendor_hardening, iam_, api_logging, dlp_,
                base_vendor_freq, mttd, mttr, downtime_cost_per_hour,
                recovery_cost, phi_records, phi_cost_per_record
            )

    heatmap = go.Figure(
        data=go.Heatmap(
            z=Z,
            x=dlp_vals,
            y=iam_vals,
            colorscale="YlOrRd",
            colorbar_title="Expected Loss (USD)"
        )
    )

    heatmap.update_layout(
        xaxis_title="DLP Coverage (%)",
        yaxis_title="IAM Restriction Strength (%)"
    )

    st.plotly_chart(heatmap, use_container_width=True)

    st.caption("All values reflect simulated academic analysis and do not represent real AHN data.")
