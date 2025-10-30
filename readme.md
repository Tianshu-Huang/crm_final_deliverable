# 🧩 AHN Ransomware Risk Dashboard
**Authors:** Evan Crooks, Mohini Madhur, Tianshu Huang  
**Course:** Cyber Risk Modeling – Group 17  
**Date:** October 2025  

---

## 📖 Overview
The **AHN Ransomware Risk Dashboard** is an interactive simulation tool designed to model and visualize the **financial and operational impacts** of ransomware on **Allegheny Health Network (AHN)**.  

Built using **Monte Carlo simulations** and a lightweight **Streamlit interface**, the dashboard helps executives and analysts explore how different cybersecurity investments — such as MFA, EDR, SOC coverage, and backup resilience — influence expected losses and recovery outcomes.

The project aligns with the goals outlined in the group’s executive summary: providing **quantitative, scenario-based insights** to improve ransomware preparedness and support **data-driven decision-making**.

---

## 🧠 Features
- 🎚️ **Interactive Controls:** Adjust security control levels (MFA coverage, SOC hours, backup strength, EDR deployment, and total budget).  
- 🎲 **Monte Carlo Simulation:** Estimates ransomware event losses using probabilistic modeling.  
- 📊 **Visual Analytics:** Displays expected annual loss (EAL), 95th-percentile loss, recovery time, and ROI.  
- ⚖️ **ROI Analysis:** Quantifies how much each investment reduces financial risk exposure.  
- 💡 **Executive Readability:** Designed for visual clarity — interpretable by both technical and non-technical audiences.

---

## 🧮 Model Logic (Simplified FAIR Framework)
Each simulation run models:
1. **Threat Event Frequency (TEF):** Likelihood of ransomware incidents per year.  
2. **Loss Magnitude (LM):** Cost of incidents drawn from a lognormal distribution (ransom, downtime, compliance fines).  
3. **Control Effectiveness:** Inputs (MFA, EDR, SOC, Backup) modify TEF and LM to simulate resilience improvements.  
4. **Outputs:** Expected Annual Loss (EAL), 95th percentile loss, estimated recovery hours, and ROI.

Example ROI interpretation:  
> An ROI of **3.0x** means each \$1 invested reduces expected loss by \$3.

---

## 🧰 Tech Stack
| Layer | Tool | Purpose |
|:--|:--|:--|
| UI / Dashboard | **Streamlit** | Interactive controls and visual layout |
| Simulation | **NumPy**, **Pandas** | Monte Carlo risk modeling |
| Visualization | **Plotly Express** | Interactive charts and histograms |
| Config Data | **CSV / JSON** | Stores control effectiveness and base assumptions |

---

## 🚀 Running the Dashboard

### 🧱 Prerequisites
- Python 3.9 or later  
- Recommended virtual environment (`venv` or `conda`)

### 📦 Install Dependencies
```bash
pip install -r requirements.txt
