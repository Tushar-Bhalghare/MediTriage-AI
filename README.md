# MediTriage AI — Automated Medical Report & Clinical Triage Copilot

> **Track:** Healthcare & Well-Being  
> **Author:** Tushar Bhalghare  
> **Platform:** MediTriage AI Clinical System  

MediTriage AI is an autonomous healthcare intelligence platform that bridges the communication gap between complex pathology diagnostic reports and anxious patients. By ingesting messy medical lab reports (blood tests, lipid profiles, Complete Blood Count, liver/kidney function tests) or raw symptom descriptions, the system executes an automated 4-stage clinical triage pipeline that translates medical jargon into plain language, flags life-threatening anomalies, and generates actionable doctor consultation protocols.

---

## 🚨 The Problem

* **Medical Jargon Asymmetry:** Over 85% of patients cannot interpret lab numbers like `HbA1c 8.4%`, `LDL 162 mg/dL`, or `ESR 38 mm/hr` without medical guidance, causing panic, delayed treatment, or unmanaged chronic diseases.
* **Clinical Overburden:** Doctors spend excessive time explaining basic reference ranges during short 5-minute consultations rather than focusing on high-level intervention.
* **Delayed Emergency Care:** Patients frequently overlook critical markers (e.g. post-prandial spikes > 240 mg/dL or acute leukocytosis), leading to emergency hospitalizations.

---

## ⚡ Automated AI Pipeline

```
[ Lab Report Scan / Photo / Symptoms ]
                  │
                  ▼
┌────────────────────────────────────────────────────────┐
│ Stage 1: Auto-OCR & Biomarker Extraction               │
│ - Digitizes messy scans & PDF reports                  │
│ - Extracts parameter names, patient values, and units  │
└────────────────────────────────────────────────────────┘
                  │
                  ▼
┌────────────────────────────────────────────────────────┐
│ Stage 2: Normalization & Pathological Anomaly Detect   │
│ - Calibrates against biological reference intervals    │
│ - Color-codes risk levels (Critical, High, Low, Normal)│
│ - Computes Cardiometabolic & Systemic Risk Index (0-100│
└────────────────────────────────────────────────────────┘
                  │
                  ▼
┌────────────────────────────────────────────────────────┐
│ Stage 3: Multi-Language Patient-Friendly Explanations  │
│ - Converts clinical jargon into plain language         │
│ - Instant toggle: English, हिंदी (Hindi), मराठी, Spanish│
│ - Integrated Web Speech API for voice narration        │
└────────────────────────────────────────────────────────┘
                  │
                  ▼
┌────────────────────────────────────────────────────────┐
│ Stage 4: Automated Clinical Triage Action Plan         │
│ - Triage Urgency Level (Emergency, Moderate, Routine) │
│ - Personalized Questions for Doctor Visit              │
│ - Evidence-based Nutrition & Lifestyle Guidance        │
│ - Exportable Clinical Presentation Summary Sheet       │
└────────────────────────────────────────────────────────┘
```

---

## 🌟 Key Features

1. **Multi-Format Input:** Upload image scans, camera photos, PDFs, or enter raw clinical symptoms.
2. **Instant Preloaded Sample Panels (1-Click Demo):**
   - 🩸 **Diabetic & Lipid Risk Panel:** High fasting blood sugar (168 mg/dL), HbA1c (8.4%), elevated LDL & triglycerides.
   - 🔬 **CBC Anemia & Infection Panel:** Low hemoglobin (9.2 g/dL), elevated WBC count (14,800 /mcL).
   - 🌿 **Annual Wellness Screen:** Optimal healthy baseline.
3. **Interactive Biomarker Matrix:** Clear table of detected markers with reference ranges and status indicators.
4. **Multilingual Plain-Language Explanations:** Toggle between English, Hindi, Marathi, and Spanish with zero latency.
5. **Voice Narration (Text-to-Speech):** Speaks the diagnosis and care plan aloud for elderly or visually impaired patients.
6. **Doctor Consultation Checklist:** Generates high-yield, specific questions for the patient to ask their physician.
7. **Personalized Nutrition Protocols:** Lists foods to embrace and strictly avoid tailored to the abnormal biomarkers.
8. **Exportable Clinical Summary:** One-click generation of a consolidated printable project sheet.

---

## 🛠️ Technology Stack

* **Backend:** Python 3, Flask
* **Image Processing & Synthesis:** Pillow (PIL)
* **Frontend:** Tailwind CSS, JavaScript (ES6+), Lucide Icons
* **Voice Engine:** Web Speech Synthesis API
* **Cloud & Database Ready:** Supabase Client & PostgreSQL Schema

---

## 🚀 How to Run Locally

1. Navigate to the project directory:
   ```powershell
   cd C:\Users\Admin\.gemini\antigravity\scratch\meditriage-ai
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Start the application:
   ```powershell
   python app.py
   # Or simply double-click start_server.bat
   ```
4. Open your browser:
   * **Local PC:** `http://127.0.0.1:5000`
   * **Mobile on Wi-Fi:** `http://192.168.1.106:5000`
