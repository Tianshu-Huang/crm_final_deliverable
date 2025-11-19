import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json

# ---------- Load Default Assumptions ----------
def load_assumptions(path="data/assumptions.csv"):
    p = Path(path)
    if not p.exists():
        return {}
    try:
        df = pd.read_csv(p)
        vals = {}
        for col in ["MTTD_hours", "MTTR_hours", "downtime_cost_per_hour"]:
            if col in df.columns:
                vals[col] = float(df[col].dropna().iloc[0])
        return vals
    except Exception:
        return {}

ASSUME = load_assumptions()

# ---------- Cost Model Functions ----------
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
    downtime_if_pay = mttd_hours + negotiation_hours + decrypt_hours
    downtime_cost_pay = downtime_if_pay * downtime_cost_per_hour
    contingency_cost = (1 - success_prob) * (
        (mttd_hours + mttr_hours) * downtime_cost_per_hour + recovery_fixed_cost
    )
    return ransom_amount + downtime_cost_pay + contingency_cost


def expected_cost_recover(
    mttd_hours: float,
    mttr_hours: float,
    downtime_cost_per_hour: float,
    recovery_fixed_cost: float,
    data_loss_cost: float = 0.0,
) -> float:
    downtime_total = mttd_hours + mttr_hours
    return downtime_total * downtime_cost_per_hour + recovery_fixed_cost + data_loss_cost


# ---------- Main Interactive Dashboard ----------
def render_decision_model_tab():
    st.title("Ransom Payment vs System Recovery — Decision Model")

    st.write(
        "This interactive dashboard compares the **expected total cost** of two strategies during a ransomware incident: "
        "**Pay Ransom** vs **Recover via Backups**. Adjust detection/recovery times, "
        "ransom amount, and success probability to visualize cost trade-offs and recommendations."
    )

    # Defaults (from assumptions file)
    default_mttd = float(ASSUME.get("MTTD_hours", 6.0))
    default_mttr = float(ASSUME.get("MTTR_hours", 18.0))
    default_downtime_cost = float(ASSUME.get("downtime_cost_per_hour", 75_000.0))

    # ---------- Sidebar Controls ----------
    st.sidebar.header("⚙️ Control Settings")

    scenario = st.sidebar.radio(
        "Scenario:",
        ["Baseline", "Optimistic", "Pessimistic"],
        key="sidebar_scenario"
    )
    mttd = st.number_input(
    "MTTD — Mean Time to Detect (hours)",
    min_value=0.0, max_value=1000.0,
    value=float(default_mttd), 
    step=1.0, 
    key="sidebar_mttd"
    )

    mttr = st.number_input(
        "MTTR — Mean Time to Recover (hours)",
        min_value=0.0, max_value=1000.0,
        value=float(default_mttr),
        step=1.0, 
        key="sidebar_mttr"
    )


    ransom_amount = st.sidebar.number_input(
    "💰 Ransom Amount (USD)", 0.0, 100_000_000.0, 1_200_000.0, step=50_000.0, key="sidebar_ransom"
    )

    success_prob = st.sidebar.slider(
        "🔐 Decryption Success Probability", 0.0, 1.0, 0.72, 0.01,
        key="sidebar_success_prob",
        help="Likelihood ransom payment successfully decrypts systems"
    )

    negotiation_hours = st.sidebar.number_input(
        "🤝 Negotiation Delay (hours)", 0.0, 168.0, 24.0, step=1.0, key="sidebar_negotiation"
    )

    decrypt_hours = st.sidebar.number_input(
        "🔓 Decryption Time (hours)", 0.0, 168.0, 12.0, step=1.0, key="sidebar_decrypt"
    )

    downtime_cost_per_hour = st.sidebar.number_input(
        "⏱️ Downtime Cost per Hour (USD)", 0.0, 5_000_000.0, default_downtime_cost, step=5_000.0, key="sidebar_downtime"
    )

    recovery_fixed_cost = st.sidebar.number_input(
        "🧰 Fixed Recovery Cost (USD)", 0.0, 50_000_000.0, 1_000_000.0, step=25_000.0, key="sidebar_fixed"
    )

    data_loss_cost = st.sidebar.number_input(
        "🗃️ Data Loss / Re-entry Cost (USD)", 0.0, 50_000_000.0, 5_000_000.0, step=25_000.0, key="sidebar_data_loss"
    )



    # Apply scenario presets
    if scenario == "Optimistic":
        success_prob = 0.95
        downtime_cost_per_hour *= 0.7
    elif scenario == "Pessimistic":
        success_prob = 0.6
        downtime_cost_per_hour *= 1.5

    # ---------- Compute Results ----------
    cost_pay = expected_cost_pay_ransom(
        ransom_amount, negotiation_hours, decrypt_hours, success_prob,
        downtime_cost_per_hour, recovery_fixed_cost, mttd, mttr
    )
    cost_recover = expected_cost_recover(
        mttd, mttr, downtime_cost_per_hour, recovery_fixed_cost, data_loss_cost
    )

    # ---------- Display Results ----------
    st.subheader("📊 Results & Recommendation")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Cost — Pay Ransom", f"${cost_pay:,.0f}")
    with c2:
        st.metric("Cost — Recover via Backups", f"${cost_recover:,.0f}")
    with c3:
        strategy = "✅ Pay Ransom" if cost_pay < cost_recover else "✅ Recover via Backups"
        st.success(strategy)

    if cost_pay < cost_recover:
        st.info(f"💰 Paying ransom is cheaper by **${cost_recover - cost_pay:,.0f}**.")
    else:
        st.info(f"🛠️ Recovering via backups is cheaper by **${cost_pay - cost_recover:,.0f}**.")

    # ---------- Tabs: Sensitivity and Heatmap----------
    tab1, tab2 = st.tabs(["📈 Sensitivity Curves", "🌡️ 2D Heatmap"])

    # --- Sensitivity: Cost vs Downtime/Hour ---
    with tab1:
        st.markdown("### Sensitivity: Cost vs. Downtime Cost per Hour")
        dc_grid = np.linspace(max(1_000.0, downtime_cost_per_hour * 0.25), downtime_cost_per_hour * 2.0, 50)
        pay_curve = [
            expected_cost_pay_ransom(ransom_amount, negotiation_hours, decrypt_hours, success_prob, dc, recovery_fixed_cost, mttd, mttr)
            for dc in dc_grid
        ]
        recover_curve = [
            expected_cost_recover(mttd, mttr, dc, recovery_fixed_cost, data_loss_cost)
            for dc in dc_grid
        ]
        df_dc = pd.DataFrame({
            "Downtime Cost / Hour (USD)": dc_grid,
            "Pay Ransom": pay_curve,
            "Recover via Backups": recover_curve
        })
        fig_dc = px.line(
            df_dc.melt(id_vars=["Downtime Cost / Hour (USD)"], var_name="Strategy", value_name="Expected Cost (USD)"),
            x="Downtime Cost / Hour (USD)", y="Expected Cost (USD)", color="Strategy"
        )
        cross_idx = np.argmin(np.abs(np.array(pay_curve) - np.array(recover_curve)))
        decision_point = dc_grid[cross_idx]
        fig_dc.add_vline(
            x=decision_point, line_dash="dash", line_color="gray",
            annotation_text=f"Break-even ≈ ${decision_point:,.0f}/hr"
        )
        st.plotly_chart(fig_dc, use_container_width=True)

    # --- 2D Sensitivity Heatmap ---
    with tab2:
        st.markdown("### Sensitivity Heatmap: MTTR vs. Success Probability")
        mttr_vals = np.arange(4, 36, 4)
        success_vals = np.arange(0.5, 1.0, 0.05)
        Z = np.zeros((len(mttr_vals), len(success_vals)))
        for i, mttr_ in enumerate(mttr_vals):
            for j, sp in enumerate(success_vals):
                Z[i, j] = expected_cost_pay_ransom(
                    ransom_amount, negotiation_hours, decrypt_hours, sp,
                    downtime_cost_per_hour, recovery_fixed_cost, mttd, mttr_
                )
        fig = go.Figure(data=go.Heatmap(
            z=Z, x=success_vals, y=mttr_vals, colorscale="YlOrRd", colorbar_title="Cost (USD)"
        ))
        fig.update_layout(
            xaxis_title="Decryption Success Probability",
            yaxis_title="MTTR (hours)"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.caption("All values are simulated for academic analysis and do not represent real AHN data.")
