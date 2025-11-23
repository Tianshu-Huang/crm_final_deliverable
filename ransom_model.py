import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

"""
Ransom Payment vs. System Recovery Model Notes & Data Sources
---------------------------------------------------------------

This file handles the "Should we pay ransom or restore systems?" decision model.
It's not meant to predict exact numbers but to show leadership how the cost
tradeoffs behave when you factor in downtime, ransom amount, and detection delays.

Where the numbers come from:

MTTD (Mean Time to Detect)
    This is estimated form past AHN attacks.
    It usually takes 30-60 days for AHN to detect a ransomware that's been sitting in its env.

MTTR (Mean Time to Recover)
    48 hours is pretty typical for ransomware restoration in hospitals.

Ransom Amount (USD)
    Typical ransom asks fall in the $1M to $5M range, so the defaults reflect that. 
    Editable through sidebar.

Decryption Success Probability
    We estimated default to 0.8 but scenario presets can change it.

Negotiation & Decryption Delays
    We estimated:
        - Negotiation roughly takes12 hours
        - Decryption roughly take 6 hours

Downtime Cost per Hour
    Estimated to be $75k/hr, aligns with hospital OR/ICU downtime numbers.

Fixed Recovery Cost
    We used ~$500k as a middle-range cost for forensics, cleanup, cloud rebuilds, IR labor, etc.

Data Loss / Re-entry Cost
    Zero by default unless the team wants to model it. This varies heavily
    by department and incident type.

Controls:
    - Scenario presets (baseline/optimistic/pessimistic)
    - Everything else is either from assumptions.csv or user input.

CSV Input:
    data/assumptions.csv holds the default MTTD/MTTR/downtime cost values.
    Users can override these to tune.

The main point of this model is not to be precise, but to compare shapes
of the cost curves and help AHN decide when ransom payment is actually the
cheaper option vs when backups win outright.
"""


# -------------------------------------------------------------------
# Load default assumptions
# -------------------------------------------------------------------
def load_assumptions(path="data/assumptions.csv"):
    """
    Load baseline assumptions for MTTD, MTTR, and downtime cost.
    Returns values found in the CSV, if present; otherwise returns empty dict.
    """
    p = Path(path)
    if not p.exists():
        return {}

    try:
        df = pd.read_csv(p)
        vals = {}

        # Only store known keys
        for col in ["MTTD_hours", "MTTR_hours", "downtime_cost_per_hour"]:
            if col in df.columns:
                vals[col] = float(df[col].dropna().iloc[0])

        return vals

    except Exception:
        return {}


# Global defaults loaded once
ASSUME = load_assumptions()


# -------------------------------------------------------------------
# Cost Model Functions (No Logic Changed)
# -------------------------------------------------------------------
def expected_cost_pay_ransom(
    ransom_amount: float,
    negotiation_hours: float,
    decrypt_hours: float,
    success_prob: float,
    downtime_cost_per_hour: float,
    recovery_fixed_cost: float,
    mttd_hours: float,
    mttr_hours: float,
) -> float:
    """
    Expected total cost if the organization chooses to pay the ransom.
    Includes ransom amount, downtime during negotiation/decryption, and
    contingency cost for failed decryption.
    """
    # Total downtime if ransom succeeds
    # CORRECT: only negotiation + decryption create downtime
    downtime_if_pay = negotiation_hours + decrypt_hours
    downtime_cost_pay = downtime_if_pay * downtime_cost_per_hour


    # Expected contingency cost if decryption fails
    contingency_cost = (1 - success_prob) * (
        (mttr_hours * downtime_cost_per_hour) + recovery_fixed_cost
    )


    return ransom_amount + downtime_cost_pay + contingency_cost


def expected_cost_recover(
    mttd_hours: float,
    mttr_hours: float,
    downtime_cost_per_hour: float,
    recovery_fixed_cost: float,
    data_loss_cost: float = 0.0,
) -> float:
    """
    Expected cost if AHN recovers systems via backup restoration.
    Includes downtime cost, fixed IR cost, and optional data-reentry cost.
    """
    downtime_total = mttr_hours
    return downtime_total * downtime_cost_per_hour + recovery_fixed_cost + data_loss_cost



# -------------------------------------------------------------------
# Main Interactive Dashboard
# -------------------------------------------------------------------
def render_decision_model_tab():
    """Render the 'Ransom vs. Recovery' decision model dashboard."""
    st.title("Ransom Payment vs System Recovery — Decision Model")

    st.write(
        "This interactive dashboard compares the **expected total cost** of two strategies "
        "during a ransomware incident: **Pay Ransom** vs **Recover via Backups**. Modify "
        "MTTD, MTTR, ransom amount, and decryption probability to visualize trade-offs."
    )

    # Load defaults from assumptions CSV
    default_mttd = float(ASSUME.get("MTTD_hours", 6.0))
    default_mttr = float(ASSUME.get("MTTR_hours", 18.0))
    default_downtime_cost = float(ASSUME.get("downtime_cost_per_hour", 75_000.0))

    # -------------------------------------------------------------
    # Sidebar Controls
    # -------------------------------------------------------------
    st.sidebar.header("⚙️ Control Settings")

    # Scenario presets
    scenario = st.sidebar.radio(
        "Scenario:",
        ["Baseline", "Optimistic", "Pessimistic"],
        key="sidebar_scenario"
    )

    # MTTD / MTTR
    mttd = st.number_input(
        "MTTD — Mean Time to Detect (hours)",
        min_value=0.0,
        max_value=1000.0,
        value=float(default_mttd),
        step=1.0,
        key="sidebar_mttd",
    )

    mttr = st.number_input(
        "MTTR — Mean Time to Recover (hours)",
        min_value=0.0,
        max_value=1000.0,
        value=float(default_mttr),
        step=1.0,
        key="sidebar_mttr",
    )

    # Ransom and decryption settings
    ransom_amount = st.sidebar.number_input(
        "Ransom Amount (USD)",
        0.0, 100_000_000.0,
        1_200_000.0,
        step=50_000.0,
        key="sidebar_ransom"
    )

    success_prob = st.sidebar.slider(
        "Decryption Success Probability",
        0.0, 1.0,
        0.72,
        0.01,
        key="sidebar_success_prob",
        help="Likelihood ransom payment successfully decrypts systems",
    )

    negotiation_hours = st.sidebar.number_input(
        "Negotiation Delay (hours)",
        0.0, 168.0,
        24.0,
        step=1.0,
        key="sidebar_negotiation"
    )

    decrypt_hours = st.sidebar.number_input(
        "Decryption Time (hours)",
        0.0, 168.0,
        12.0,
        step=1.0,
        key="sidebar_decrypt"
    )

    downtime_cost_per_hour = st.sidebar.number_input(
        "Downtime Cost per Hour (USD)",
        0.0, 5_000_000.0,
        default_downtime_cost,
        step=5_000.0,
        key="sidebar_downtime"
    )

    # IR and data-loss cost
    recovery_fixed_cost = st.sidebar.number_input(
        "Fixed Recovery Cost (USD)",
        0.0, 50_000_000.0,
        1_000_000.0,
        step=25_000.0,
        key="sidebar_fixed"
    )

    data_loss_cost = st.sidebar.number_input(
        "Data Loss / Re-entry Cost (USD)",
        0.0, 50_000_000.0,
        5_000_000.0,
        step=25_000.0,
        key="sidebar_data_loss"
    )

    # -------------------------------------------------------------
    # Apply Scenario Presets (Logic unchanged)
    # -------------------------------------------------------------
    if scenario == "Optimistic":
        success_prob = 0.95
        downtime_cost_per_hour *= 0.7

    elif scenario == "Pessimistic":
        success_prob = 0.6
        downtime_cost_per_hour *= 1.5

    # -------------------------------------------------------------
    # Compute Cost for Both Strategies
    # -------------------------------------------------------------
    cost_pay = expected_cost_pay_ransom(
        ransom_amount, negotiation_hours, decrypt_hours, success_prob,
        downtime_cost_per_hour, recovery_fixed_cost, mttd, mttr
    )

    cost_recover = expected_cost_recover(
        mttd, mttr, downtime_cost_per_hour, recovery_fixed_cost, data_loss_cost
    )

    # -------------------------------------------------------------
    # Display Primary Results
    # -------------------------------------------------------------
    st.subheader("Results & Recommendation")

    c1, c2, c3 = st.columns(3)
    c1.metric("Cost — Pay Ransom", f"${cost_pay:,.0f}")
    c2.metric("Cost — Recover via Backups", f"${cost_recover:,.0f}")

    strategy = "✅ Pay Ransom" if cost_pay < cost_recover else "✅ Recover via Backups"
    with c3:
        st.success(strategy)

    # Comparison message
    if cost_pay < cost_recover:
        st.info(f"Paying ransom is cheaper by **${cost_recover - cost_pay:,.0f}**.")
    else:
        st.info(f"Recovering via backups is cheaper by **${cost_pay - cost_recover:,.0f}**.")

    # -------------------------------------------------------------
    # Tabs: Sensitivity Analysis + Heatmap
    # -------------------------------------------------------------
    tab1, tab2 = st.tabs(["📈 Sensitivity Curves", "🌡️ 2D Heatmap"])

    # ---------------- Sensitivity Curves ----------------
    with tab1:
        st.markdown("### Sensitivity: Cost vs. Downtime Cost per Hour")

        # Generate sensitivity grid
        dc_grid = np.linspace(
            max(1_000.0, downtime_cost_per_hour * 0.25),
            downtime_cost_per_hour * 2.0,
            50
        )

        # Compute curves
        pay_curve = [
            expected_cost_pay_ransom(
                ransom_amount, negotiation_hours, decrypt_hours, success_prob,
                dc, recovery_fixed_cost, mttd, mttr
            )
            for dc in dc_grid
        ]

        recover_curve = [
            expected_cost_recover(
                mttd, mttr, dc, recovery_fixed_cost, data_loss_cost
            )
            for dc in dc_grid
        ]

        # Prepare dataframe for Plotly
        df_dc = pd.DataFrame({
            "Downtime Cost / Hour (USD)": dc_grid,
            "Pay Ransom": pay_curve,
            "Recover via Backups": recover_curve
        })

        fig_dc = px.line(
            df_dc.melt(
                id_vars=["Downtime Cost / Hour (USD)"],
                var_name="Strategy",
                value_name="Expected Cost (USD)"
            ),
            x="Downtime Cost / Hour (USD)",
            y="Expected Cost (USD)",
            color="Strategy"
        )

        # Identify break-even point
        cross_idx = np.argmin(np.abs(np.array(pay_curve) - np.array(recover_curve)))
        decision_point = dc_grid[cross_idx]

        fig_dc.add_vline(
            x=decision_point,
            line_dash="dash",
            line_color="gray",
            annotation_text=f"Break-even ≈ ${decision_point:,.0f}/hr"
        )

        st.plotly_chart(fig_dc, use_container_width=True)

    # ---------------- 2D Heatmap ----------------
    with tab2:
        st.markdown("### Sensitivity Heatmap: MTTR vs. Success Probability")

        mttr_vals = np.arange(4, 36, 4)
        success_vals = np.arange(0.5, 1.0, 0.05)

        # Z[i, j] = cost of paying ransom at MTTR=mttr_vals[i], SP=success_vals[j]
        Z = np.zeros((len(mttr_vals), len(success_vals)))

        for i, mttr_ in enumerate(mttr_vals):
            for j, sp in enumerate(success_vals):
                Z[i, j] = expected_cost_pay_ransom(
                    ransom_amount, negotiation_hours, decrypt_hours, sp,
                    downtime_cost_per_hour, recovery_fixed_cost, mttd, mttr_
                )

        fig = go.Figure(
            data=go.Heatmap(
                z=Z, x=success_vals, y=mttr_vals,
                colorscale="YlOrRd",
                colorbar_title="Cost (USD)"
            )
        )

        fig.update_layout(
            xaxis_title="Decryption Success Probability",
            yaxis_title="MTTR (hours)"
        )

        st.plotly_chart(fig, use_container_width=True)

    st.caption("All values are simulated for academic analysis and do not represent real AHN data.")
