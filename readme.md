# AHN Ransomware Risk Dashboard

An interactive simulation tool designed to help Allegheny Health Network (AHN) leadership understand and quantify ransomware risk, evaluate security control investments, and explore financial/operational outcomes under multiple scenarios. Built for CMU Heinz College Cyber Risk Modeling (CRM) — Group 17.

---

## 📌 Overview
This dashboard models ransomware risk using Monte Carlo simulation and visualizes:
- **Expected Annual Loss (EAL)**
- **Tail risk (95th percentile losses)**
- **Recovery time estimates**
- **Return on Investment (ROI) of security controls**
- **Scenario comparisons**

The tool supports multiple scenarios including:
- Ransomware (primary model)
- Phishing-based intrusion
- Vendor / supply-chain compromise (coming soon!
)

---

## 🧠 How It Works
The simulation is based on a simplified FAIR-style model:
- **Frequency** of attacks (TEF)
- **Loss magnitude** distribution (LM)
- **Control effectiveness** modifying both frequency and severity

Controls modeled include:
- **MFA coverage**
- **EDR deployment**
- **SOC monitoring hours / coverage**
- **Backup strength (RPO/RTO)**

The underlying engine is implemented in `ransom_model.py`. Inputs and assumptions are loaded from `data/simulation_inputs.csv`.

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/Tianshu-Huang/crm_final_deliverable.git
cd crm_final_deliverable
```

### 2. Create a Virtual Environment (optional but recommended)
```bash
python -m venv venv
source venv/bin/activate     # macOS/Linux
venv\Scripts\activate        # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Launch the Dashboard
```bash
streamlit run app.py
```
Then open your browser to:
```
http://localhost:8501
```

---

## 🖥️ Dashboard Features

### **1. Control Panel (Left Sidebar)**
Adjust organization-specific cybersecurity parameters:
- MFA coverage (%)
- EDR deployment level (%)
- SOC monitoring hours (0–24)
- Backup resilience / RTO
- Budget allocation sliders

These directly update the simulation parameters.

---

### **2. Monte Carlo Simulation Outputs**
Displayed in interactive visualizations:

#### **Expected Annual Loss (EAL)**
The model estimates mean annualized damages from ransomware.

#### **Loss Distribution Histogram**
Displaying fat-tail risks and uncertainties.

#### **95th Percentile Loss (P95)**
Useful for extreme—but plausible—risk planning.

#### **Recovery Time Estimates**
Based on backup/RTO inputs.

#### **Return on Investment (ROI)**
Quantifies how much loss reduction each security investment produces.

---

### **3. Scenario Comparison**
Users can:
- Save baseline settings
- Adjust control parameters
- Compare results against another scenario

This helps leadership make informed budget decisions.

---

## 📂 Project Structure
```
crm_final_deliverable/
│
├── app.py                  # Streamlit entry point
├── main_dashboard.py       # UI layout + dashboard orchestration
├── ransom_model.py         # Monte Carlo risk engine
├── scenario_phishing.py    # Phishing intrusion scenario
├── scenario_vendor.py      # Vendor compromise scenario (if implemented)
│
├── requirements.txt        # Dependencies
├── README.md               # This file
│
└── data/
    ├── simulation_inputs.csv  # TEF/LM baseline values & control defaults
    └── assumptions.csv        # (Optional) supplementary inputs
```

---

## 📊 Example Usage

### **Scenario:** Increasing MFA coverage from 60% → 90%
1. Launch the dashboard
2. Set MFA slider to **90%**
3. Keep other controls constant
4. Run simulation
5. Observe:
   - Change in EAL
   - Reduction in tail risk
   - ROI in relation to cost

This allows actionable, data-driven insights for leadership.

---

## 🧪 Modifying Assumptions
You can update inputs in:
```
data/simulation_inputs.csv
```
This file contains:
- Baseline frequency
- Loss distribution parameters (µ, σ)
- Control default settings
- Ransom baseline cost

If new data becomes available (e.g., from AHN logs), adjust these values to better reflect real-world posture.

---

## 🛠️ Extending the Model
You can add:
- New controls (e.g., segmentation, training effectiveness)
- New threat scenarios
- New visualization panels

Steps:
1. Add logic inside `ransom_model.py`
2. Add UI controls in `main_dashboard.py`
3. Update simulation input files

---

## ⚠️ Limitations
- Model does not capture correlated multi-site outages
- Real-world effectiveness of controls varies by threat actor
- Recovery-time estimates rely on simplified backup assumptions
- Use results as **decision support**, not deterministic truth

---

## 🙋‍♀️ Authors
**CRM Group 17 (Fall 2025)**
- Tianshu Huang
- Evan Crooks
- Mohini Madhur

Carnegie Mellon University — Heinz College

---

If you'd like:
- A bilingual (EN/中文) README
- Version with diagrams
- A more executive-friendly version

Just tell me and I’ll generate it!

