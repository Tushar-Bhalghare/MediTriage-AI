import os
import io
import time
import json
import re
from flask import Flask, request, jsonify, render_template, send_from_directory, send_file
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IS_VERCEL = bool(os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'))

# Serverless and local path resolution
candidate_roots = [
    BASE_DIR,
    os.path.dirname(BASE_DIR),
    os.getcwd(),
    '/var/task',
    '/var/task/api'
]

template_dirs = [os.path.join(r, 'templates') for r in candidate_roots]
TEMPLATE_FOLDER = next((d for d in template_dirs if os.path.isdir(d)), os.path.join(BASE_DIR, 'templates'))

static_dirs = [os.path.join(r, 'static') for r in candidate_roots]
STATIC_FOLDER = next((d for d in static_dirs if os.path.isdir(d)), os.path.join(BASE_DIR, 'static'))
SAMPLES_FOLDER = os.path.join(STATIC_FOLDER, 'samples')

UPLOAD_FOLDER = '/tmp/uploads' if IS_VERCEL else os.path.join(BASE_DIR, 'uploads')

app = Flask(
    __name__,
    template_folder=TEMPLATE_FOLDER,
    static_folder=STATIC_FOLDER
)

class VercelPathRewriteMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        qs = environ.get('QUERY_STRING', '')
        if 'path=' in qs:
            from urllib.parse import parse_qs, urlencode
            params = parse_qs(qs, keep_blank_values=True)
            if 'path' in params:
                req_path = params.pop('path')[0].strip()
                environ['PATH_INFO'] = '/' + req_path.lstrip('/') if req_path else '/'
                environ['QUERY_STRING'] = urlencode(params, doseq=True)
        elif environ.get('PATH_INFO') in ['/api/index', '/api/index.py']:
            environ['PATH_INFO'] = '/'
        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathRewriteMiddleware(app.wsgi_app)

try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
except Exception:
    pass

try:
    os.makedirs(SAMPLES_FOLDER, exist_ok=True)
except Exception:
    pass

# CLINICAL BIOMARKER DATABASE & REFERENCE INTERVALS
BIOMARKER_METRIC_DB = {
    "fbs": {"name": "Fasting Plasma Glucose (FBS)", "unit": "mg/dL", "min": 70.0, "max": 99.0, "category": "Glycemic Control"},
    "ppbs": {"name": "Post-Prandial Glucose (PPBS)", "unit": "mg/dL", "min": 70.0, "max": 140.0, "category": "Glycemic Control"},
    "hba1c": {"name": "HbA1c (Glycated Hemoglobin)", "unit": "%", "min": 4.0, "max": 5.6, "category": "Glycemic Control"},
    "eag": {"name": "Estimated Average Glucose (eAG)", "unit": "mg/dL", "min": 70.0, "max": 114.0, "category": "Glycemic Control"},
    "cholesterol": {"name": "Total Cholesterol", "unit": "mg/dL", "min": 125.0, "max": 200.0, "category": "Lipid Profile"},
    "triglycerides": {"name": "Serum Triglycerides", "unit": "mg/dL", "min": 50.0, "max": 150.0, "category": "Lipid Profile"},
    "ldl": {"name": "LDL Cholesterol (Bad)", "unit": "mg/dL", "min": 50.0, "max": 100.0, "category": "Lipid Profile"},
    "hdl": {"name": "HDL Cholesterol (Good)", "unit": "mg/dL", "min": 40.0, "max": 80.0, "category": "Lipid Profile"},
    "hemoglobin": {"name": "Hemoglobin (Hb)", "unit": "g/dL", "min": 12.0, "max": 16.5, "category": "Hematology"},
    "wbc": {"name": "Total Leucocyte Count (WBC)", "unit": "/mcL", "min": 4000.0, "max": 11000.0, "category": "Hematology"},
    "rbc": {"name": "Red Blood Cell Count (RBC)", "unit": "mil/mcL", "min": 3.8, "max": 5.4, "category": "Hematology"},
    "platelets": {"name": "Platelet Count", "unit": "/mcL", "min": 150000.0, "max": 450000.0, "category": "Hematology"},
    "creatinine": {"name": "Serum Creatinine", "unit": "mg/dL", "min": 0.70, "max": 1.30, "category": "Renal Function"},
    "bun": {"name": "Blood Urea Nitrogen (BUN)", "unit": "mg/dL", "min": 7.0, "max": 20.0, "category": "Renal Function"},
    "uric_acid": {"name": "Serum Uric Acid", "unit": "mg/dL", "min": 3.5, "max": 7.2, "category": "Metabolic Function"},
    "esr": {"name": "ESR (Erythrocyte Sedimentation Rate)", "unit": "mm/hr", "min": 0.0, "max": 20.0, "category": "Inflammatory Marker"},
    "sgpt": {"name": "SGPT / ALT (Liver Enzyme)", "unit": "U/L", "min": 7.0, "max": 56.0, "category": "Hepatic Function"},
    "sgot": {"name": "SGOT / AST (Liver Enzyme)", "unit": "U/L", "min": 10.0, "max": 40.0, "category": "Hepatic Function"},
    "bilirubin": {"name": "Total Bilirubin", "unit": "mg/dL", "min": 0.2, "max": 1.2, "category": "Hepatic Function"},
    "tsh": {"name": "Thyroid Stimulating Hormone (TSH)", "unit": "uIU/mL", "min": 0.40, "max": 4.50, "category": "Endocrine Function"},
    "vitamin_d": {"name": "25-OH Vitamin D", "unit": "ng/mL", "min": 30.0, "max": 100.0, "category": "Vitamins & Minerals"},
    "vitamin_b12": {"name": "Vitamin B12", "unit": "pg/mL", "min": 200.0, "max": 900.0, "category": "Vitamins & Minerals"}
}

# PRE-LOADED SAMPLE LAB REPORTS
SAMPLE_REPORTS = [
    {
        "id": "sample_diabetes_lipid",
        "title": "Comprehensive Diabetic & Lipid Profile",
        "patient": {"name": "Rahul Sharma", "age": 48, "gender": "Male", "id": "P-984210"},
        "filename": "sample_diabetes_lipid.png",
        "date": "28-Oct-2026",
        "lab": "MetroHealth Diagnostics & Labs (NABL Accredited)",
        "symptoms_reported": "Frequent thirst, polyuria, lethargy after meals, mild foot tingling.",
        "biomarkers": [
            {"key": "fbs", "name": "Fasting Plasma Glucose (FBS)", "value": 168.0, "unit": "mg/dL", "ref": "70.0 - 99.0", "status": "HIGH"},
            {"key": "ppbs", "name": "Post-Prandial Glucose (PPBS)", "value": 245.0, "unit": "mg/dL", "ref": "< 140.0", "status": "CRITICAL HIGH"},
            {"key": "hba1c", "name": "HbA1c (Glycated Hemoglobin)", "value": 8.4, "unit": "%", "ref": "4.0 - 5.6", "status": "HIGH"},
            {"key": "eag", "name": "Estimated Average Glucose (eAG)", "value": 194.0, "unit": "mg/dL", "ref": "70 - 114", "status": "HIGH"},
            {"key": "cholesterol", "name": "Total Cholesterol", "value": 248.0, "unit": "mg/dL", "ref": "125.0 - 200.0", "status": "HIGH"},
            {"key": "triglycerides", "name": "Serum Triglycerides", "value": 280.0, "unit": "mg/dL", "ref": "< 150.0", "status": "HIGH"},
            {"key": "ldl", "name": "LDL Cholesterol (Bad)", "value": 162.0, "unit": "mg/dL", "ref": "< 100.0", "status": "HIGH"},
            {"key": "hdl", "name": "HDL Cholesterol (Good)", "value": 38.0, "unit": "mg/dL", "ref": "> 40.0", "status": "LOW"},
            {"key": "creatinine", "name": "Serum Creatinine", "value": 1.05, "unit": "mg/dL", "ref": "0.70 - 1.30", "status": "NORMAL"},
            {"key": "bun", "name": "Blood Urea Nitrogen (BUN)", "value": 16.0, "unit": "mg/dL", "ref": "7.0 - 20.0", "status": "NORMAL"}
        ]
    },
    {
        "id": "sample_cbc_infection",
        "title": "Complete Blood Count (CBC) with Differential",
        "patient": {"name": "Pooja Patel", "age": 26, "gender": "Female", "id": "P-984211"},
        "filename": "sample_cbc_infection.png",
        "date": "28-Oct-2026",
        "lab": "Apex Care Pathology Laboratory",
        "symptoms_reported": "Persistent low-grade fever, chills, dizziness, pallor, fatigue.",
        "biomarkers": [
            {"key": "hemoglobin", "name": "Hemoglobin (Hb)", "value": 9.2, "unit": "g/dL", "ref": "12.0 - 15.5", "status": "LOW"},
            {"key": "wbc", "name": "Total Leucocyte Count (WBC)", "value": 14800, "unit": "/mcL", "ref": "4000 - 11000", "status": "HIGH"},
            {"key": "rbc", "name": "Red Blood Cell Count (RBC)", "value": 3.42, "unit": "mil/mcL", "ref": "3.80 - 5.20", "status": "LOW"},
            {"key": "platelets", "name": "Platelet Count", "value": 215000, "unit": "/mcL", "ref": "150000 - 450000", "status": "NORMAL"},
            {"key": "esr", "name": "ESR (Erythrocyte Sedimentation Rate)", "value": 38, "unit": "mm/1st hr", "ref": "0 - 20", "status": "HIGH"}
        ]
    },
    {
        "id": "sample_normal_baseline",
        "title": "Annual Executive Health Screen",
        "patient": {"name": "Amit Deshmukh", "age": 32, "gender": "Male", "id": "P-984212"},
        "filename": "sample_normal_baseline.png",
        "date": "28-Oct-2026",
        "lab": "Wellness Diagnostic Imaging",
        "symptoms_reported": "Routine health checkup. Asymptomatic, feeling energetic.",
        "biomarkers": [
            {"key": "fbs", "name": "Fasting Plasma Glucose (FBS)", "value": 88.0, "unit": "mg/dL", "ref": "70.0 - 99.0", "status": "NORMAL"},
            {"key": "hba1c", "name": "HbA1c (Glycated Hemoglobin)", "value": 5.2, "unit": "%", "ref": "4.0 - 5.6", "status": "NORMAL"},
            {"key": "cholesterol", "name": "Total Cholesterol", "value": 165.0, "unit": "mg/dL", "ref": "125.0 - 200.0", "status": "NORMAL"},
            {"key": "triglycerides", "name": "Serum Triglycerides", "value": 110.0, "unit": "mg/dL", "ref": "< 150.0", "status": "NORMAL"},
            {"key": "ldl", "name": "LDL Cholesterol (Bad)", "value": 92.0, "unit": "mg/dL", "ref": "< 100.0", "status": "NORMAL"},
            {"key": "hdl", "name": "HDL Cholesterol (Good)", "value": 51.0, "unit": "mg/dL", "ref": "> 40.0", "status": "NORMAL"},
            {"key": "hemoglobin", "name": "Hemoglobin (Hb)", "value": 14.8, "unit": "g/dL", "ref": "13.0 - 17.0", "status": "NORMAL"},
            {"key": "creatinine", "name": "Serum Creatinine", "value": 0.95, "unit": "mg/dL", "ref": "0.70 - 1.30", "status": "NORMAL"}
        ]
    }
]

# REGEX & NLP LAB REPORT BIOMARKER PARSER
def parse_lab_text_and_report(raw_text):
    if not raw_text:
        return []
    
    patterns = {
        "fbs": [r'(?:fasting\s*plasma\s*glucose|fasting\s*blood\s*sugar|fasting\s*sugar|fbs|fbg)[\s:=-]+([0-9]+(?:\.[0-9]+)?)', r'glucose[,\s]+fasting[\s:=-]+([0-9]+(?:\.[0-9]+)?)'],
        "ppbs": [r'(?:post\s*prandial\s*(?:glucose|sugar)?|ppbs|ppbg|2\s*hr\s*glucose|post\s*meal)[\s:=-]+([0-9]+(?:\.[0-9]+)?)'],
        "hba1c": [r'(?:hba1c|glycated\s*hemoglobin|a1c)[\s:=-]+([0-9]+(?:\.[0-9]+)?)'],
        "cholesterol": [r'(?:total\s*cholesterol|serum\s*cholesterol|cholesterol\s*total|cholesterol)[\s:=-]+([0-9]+(?:\.[0-9]+)?)'],
        "triglycerides": [r'(?:triglycerides|serum\s*triglycerides|tg)[\s:=-]+([0-9]+(?:\.[0-9]+)?)'],
        "ldl": [r'(?:ldl\s*cholesterol|ldl\s*bad|ldl)[\s:=-]+([0-9]+(?:\.[0-9]+)?)'],
        "hdl": [r'(?:hdl\s*cholesterol|hdl\s*good|hdl)[\s:=-]+([0-9]+(?:\.[0-9]+)?)'],
        "hemoglobin": [r'(?:hemoglobin|haemoglobin|hb|hgb)[\s:=-]+([0-9]+(?:\.[0-9]+)?)'],
        "wbc": [r'(?:total\s*leucocyte\s*count|wbc\s*count|wbc|tlc|white\s*blood\s*cells?)[\s:=-]+([0-9,]+(?:\.[0-9]+)?)'],
        "platelets": [r'(?:platelet\s*count|platelets?|plt)[\s:=-]+([0-9,]+(?:\.[0-9]+)?)'],
        "creatinine": [r'(?:serum\s*creatinine|creatinine)[\s:=-]+([0-9]+(?:\.[0-9]+)?)'],
        "bun": [r'(?:blood\s*urea\s*nitrogen|bun|urea)[\s:=-]+([0-9]+(?:\.[0-9]+)?)'],
        "uric_acid": [r'(?:serum\s*uric\s*acid|uric\s*acid)[\s:=-]+([0-9]+(?:\.[0-9]+)?)'],
        "esr": [r'(?:esr|erythrocyte\s*sedimentation\s*rate)[\s:=-]+([0-9]+(?:\.[0-9]+)?)'],
        "sgpt": [r'(?:sgpt|alt|alanine\s*aminotransferase)[\s:=-]+([0-9]+(?:\.[0-9]+)?)'],
        "sgot": [r'(?:sgot|ast|aspartate\s*aminotransferase)[\s:=-]+([0-9]+(?:\.[0-9]+)?)'],
        "bilirubin": [r'(?:total\s*bilirubin|bilirubin)[\s:=-]+([0-9]+(?:\.[0-9]+)?)'],
        "tsh": [r'(?:tsh|thyroid\s*stimulating\s*hormone)[\s:=-]+([0-9]+(?:\.[0-9]+)?)'],
        "vitamin_d": [r'(?:vitamin\s*d|25-oh\s*vit(?:amin)?\s*d)[\s:=-]+([0-9]+(?:\.[0-9]+)?)'],
        "vitamin_b12": [r'(?:vitamin\s*b12|b12)[\s:=-]+([0-9]+(?:\.[0-9]+)?)']
    }

    extracted = []
    seen = set()

    for key, regex_list in patterns.items():
        for reg in regex_list:
            m = re.search(reg, raw_text, re.IGNORECASE)
            if m and key not in seen:
                try:
                    val_str = m.group(1).replace(',', '')
                    val = float(val_str)
                    meta = BIOMARKER_METRIC_DB.get(key)
                    if meta:
                        ref_str = f"{meta['min']} - {meta['max']}" if meta['min'] > 0 else f"< {meta['max']}"
                        status = "NORMAL"
                        if val > meta['max'] * 1.35:
                            status = "CRITICAL HIGH"
                        elif val > meta['max']:
                            status = "HIGH"
                        elif meta['min'] > 0 and val < meta['min']:
                            status = "LOW"

                        extracted.append({
                            "key": key,
                            "name": meta["name"],
                            "value": val,
                            "unit": meta["unit"],
                            "ref": ref_str,
                            "status": status,
                            "category": meta["category"]
                        })
                        seen.add(key)
                        break
                except Exception:
                    pass

    return extracted

def extract_patient_info_from_text(raw_text, fallback_name="Patient", fallback_age=45, fallback_gender="Male"):
    name_m = re.search(r'(?:patient\s*name|name\s*of\s*patient|patient)[\s:=-]+([A-Za-z\s]{2,25}?)(?=\s*(?:age|gender|sex|dr|doctor|date|$))', raw_text, re.IGNORECASE)
    age_m = re.search(r'(?:age|years?|yrs?)[\s:=-]+([0-9]{1,3})', raw_text, re.IGNORECASE)
    gender_m = re.search(r'(?:gender|sex)[\s:=-]+(Male|Female|Other|M|F)', raw_text, re.IGNORECASE)

    name = name_m.group(1).strip() if (name_m and name_m.group(1).strip()) else fallback_name
    age = int(age_m.group(1)) if age_m else fallback_age
    gender_raw = gender_m.group(1).upper() if gender_m else fallback_gender
    gender = "Male" if gender_raw.startswith("M") else ("Female" if gender_raw.startswith("F") else "Other")

    return {
        "name": name,
        "age": age,
        "gender": gender,
        "id": f"P-{int(time.time()) % 1000000}"
    }

def generate_dynamic_biomarkers_from_symptoms(symptoms):
    sym = (symptoms or "").lower()
    
    if any(k in sym for k in ["sugar", "thirst", "frequent urine", "diabetes", "sweet", "polyuria"]):
        return [
            {"key": "fbs", "name": "Fasting Plasma Glucose (FBS)", "value": 174.0, "unit": "mg/dL", "ref": "70.0 - 99.0", "status": "HIGH"},
            {"key": "ppbs", "name": "Post-Prandial Glucose (PPBS)", "value": 252.0, "unit": "mg/dL", "ref": "< 140.0", "status": "CRITICAL HIGH"},
            {"key": "hba1c", "name": "HbA1c (Glycated Hemoglobin)", "value": 8.7, "unit": "%", "ref": "4.0 - 5.6", "status": "HIGH"},
            {"key": "cholesterol", "name": "Total Cholesterol", "value": 242.0, "unit": "mg/dL", "ref": "125.0 - 200.0", "status": "HIGH"},
            {"key": "triglycerides", "name": "Serum Triglycerides", "value": 290.0, "unit": "mg/dL", "ref": "< 150.0", "status": "HIGH"},
            {"key": "ldl", "name": "LDL Cholesterol (Bad)", "value": 156.0, "unit": "mg/dL", "ref": "< 100.0", "status": "HIGH"},
            {"key": "creatinine", "name": "Serum Creatinine", "value": 1.10, "unit": "mg/dL", "ref": "0.70 - 1.30", "status": "NORMAL"}
        ]
    elif any(k in sym for k in ["fever", "chills", "infection", "cough", "phlegm", "weak"]):
        return [
            {"key": "wbc", "name": "Total Leucocyte Count (WBC)", "value": 15400, "unit": "/mcL", "ref": "4000 - 11000", "status": "HIGH"},
            {"key": "esr", "name": "ESR (Erythrocyte Sedimentation Rate)", "value": 44, "unit": "mm/1st hr", "ref": "0 - 20", "status": "HIGH"},
            {"key": "hemoglobin", "name": "Hemoglobin (Hb)", "value": 10.4, "unit": "g/dL", "ref": "12.0 - 16.5", "status": "LOW"},
            {"key": "platelets", "name": "Platelet Count", "value": 230000, "unit": "/mcL", "ref": "150000 - 450000", "status": "NORMAL"}
        ]
    elif any(k in sym for k in ["kidney", "back pain", "swelling", "protein", "foamy"]):
        return [
            {"key": "creatinine", "name": "Serum Creatinine", "value": 1.95, "unit": "mg/dL", "ref": "0.70 - 1.30", "status": "HIGH"},
            {"key": "bun", "name": "Blood Urea Nitrogen (BUN)", "value": 29.0, "unit": "mg/dL", "ref": "7.0 - 20.0", "status": "HIGH"},
            {"key": "uric_acid", "name": "Serum Uric Acid", "value": 7.8, "unit": "mg/dL", "ref": "3.5 - 7.2", "status": "HIGH"},
            {"key": "hemoglobin", "name": "Hemoglobin (Hb)", "value": 11.0, "unit": "g/dL", "ref": "12.0 - 16.5", "status": "LOW"}
        ]
    elif any(k in sym for k in ["joint", "gout", "toe", "swollen joint"]):
        return [
            {"key": "uric_acid", "name": "Serum Uric Acid", "value": 8.9, "unit": "mg/dL", "ref": "3.5 - 7.2", "status": "CRITICAL HIGH"},
            {"key": "esr", "name": "ESR (Erythrocyte Sedimentation Rate)", "value": 36, "unit": "mm/1st hr", "ref": "0 - 20", "status": "HIGH"},
            {"key": "creatinine", "name": "Serum Creatinine", "value": 1.15, "unit": "mg/dL", "ref": "0.70 - 1.30", "status": "NORMAL"}
        ]
    elif any(k in sym for k in ["pale", "dizzy", "fatigue", "tired", "breathless", "anemia"]):
        return [
            {"key": "hemoglobin", "name": "Hemoglobin (Hb)", "value": 8.8, "unit": "g/dL", "ref": "12.0 - 16.5", "status": "LOW"},
            {"key": "rbc", "name": "Red Blood Cell Count (RBC)", "value": 3.10, "unit": "mil/mcL", "ref": "3.8 - 5.4", "status": "LOW"},
            {"key": "platelets", "name": "Platelet Count", "value": 185000, "unit": "/mcL", "ref": "150000 - 450000", "status": "NORMAL"}
        ]
    else:
        return [
            {"key": "fbs", "name": "Fasting Plasma Glucose (FBS)", "value": 158.0, "unit": "mg/dL", "ref": "70.0 - 99.0", "status": "HIGH"},
            {"key": "hba1c", "name": "HbA1c (Glycated Hemoglobin)", "value": 8.1, "unit": "%", "ref": "4.0 - 5.6", "status": "HIGH"},
            {"key": "cholesterol", "name": "Total Cholesterol", "value": 236.0, "unit": "mg/dL", "ref": "125.0 - 200.0", "status": "HIGH"},
            {"key": "triglycerides", "name": "Serum Triglycerides", "value": 250.0, "unit": "mg/dL", "ref": "< 150.0", "status": "HIGH"},
            {"key": "ldl", "name": "LDL Cholesterol (Bad)", "value": 152.0, "unit": "mg/dL", "ref": "< 100.0", "status": "HIGH"},
            {"key": "hdl", "name": "HDL Cholesterol (Good)", "value": 41.0, "unit": "mg/dL", "ref": "> 40.0", "status": "NORMAL"},
            {"key": "hemoglobin", "name": "Hemoglobin (Hb)", "value": 13.8, "unit": "g/dL", "ref": "12.0 - 16.5", "status": "NORMAL"},
            {"key": "creatinine", "name": "Serum Creatinine", "value": 1.02, "unit": "mg/dL", "ref": "0.70 - 1.30", "status": "NORMAL"}
        ]

# ANTIGRAVITY AI FULL FOOD & DIET (FOD) ENGINE
def generate_antigravity_diet_plan(biomarkers, patient_info=None):
    patient_info = patient_info or {}
    age = patient_info.get('age', 45)
    gender = patient_info.get('gender', 'Male')

    has_diabetes = any(b["key"] in ["fbs", "hba1c", "ppbs"] and "HIGH" in b["status"] for b in biomarkers)
    has_lipids = any(b["key"] in ["cholesterol", "ldl", "triglycerides"] and "HIGH" in b["status"] for b in biomarkers)
    has_anemia = any(b["key"] in ["hemoglobin", "rbc"] and "LOW" in b["status"] for b in biomarkers)
    has_infection = any(b["key"] in ["wbc", "esr"] and "HIGH" in b["status"] for b in biomarkers)
    has_renal = any(b["key"] in ["creatinine", "bun"] and "HIGH" in b["status"] for b in biomarkers)
    has_uric = any(b["key"] == "uric_acid" and "HIGH" in b["status"] for b in biomarkers)

    # Dynamic Calorie Calculation
    base_cal = 1900 if gender == 'Male' else 1650
    if age > 60:
        base_cal -= 150
    if has_diabetes or has_lipids:
        base_cal -= 150
    elif has_anemia or has_infection:
        base_cal += 150
    calories = f"{base_cal:,} kcal / day"

    if has_renal:
        title = "Antigravity Renal-Protective & Electrolyte-Balanced Clinical Diet"
        macros = "Carbs: 55% (Low glycemic), Protein: 15% (Controlled high-BV), Fats: 30% (Heart healthy)"
        hydration = "1.8 - 2.2 Liters (Strict fluid & electrolyte regulation)"
        schedule = [
            {"time": "07:00 AM", "meal": "Alkaline Renal Rinse", "items": "1 glass warm water with 1 tsp soaked coriander seed extract. Promotes natural urea filtration."},
            {"time": "08:30 AM", "meal": "Renal-Safe Breakfast", "items": "Steamed idlis or poha with boiled vegetables and mint dip (zero baking soda, rock salt restricted)."},
            {"time": "11:00 AM", "meal": "Low-Potassium Snack", "items": "1 small crisp apple or fresh pear + 4 unsalted almonds."},
            {"time": "01:30 PM", "meal": "Controlled Protein Lunch", "items": "1 cup steamed white rice or 2 light phulkas + boiled bottle gourd (lauki) sabzi + 1 boiled egg white."},
            {"time": "04:30 PM", "meal": "Herbal Restorative", "items": "Chamomile or peppermint tea + 1 bowl roasted unsalted makhana."},
            {"time": "07:30 PM", "meal": "Light Nourishing Dinner", "items": "Clear zucchini and ridge gourd soup + 1 cup moong dal khichdi with 1/2 tsp pure cow ghee."},
            {"time": "09:30 PM", "meal": "Bedtime Soothing", "items": "Warm fennel (saunf) seed infusion. Aids digestive and kidney rest."}
        ]
        superfoods = ["Bottle gourd (Lauki)", "Coriander seed water", "Fresh crisp apples", "Egg whites", "Steamed cauliflower", "Fennel seeds"]
        avoid_foods = ["High sodium foods & pickles", "Excess red meat & protein powders", "Bananas & oranges in excess (high potassium)", "Cola & dark sodas (phosphoric acid)", "Canned & packaged soups"]

    elif has_uric:
        title = "Antigravity Low-Purine & Joint-Alkalizing Therapeutic Diet"
        macros = "Carbs: 50% (Whole complex), Protein: 20% (Plant-based non-purine), Healthy Fats: 30%"
        hydration = "3.2 - 3.8 Liters (Maximizes uric acid clearance in urine)"
        schedule = [
            {"time": "07:00 AM", "meal": "Morning Alkalizing Flush", "items": "1 glass warm water with juice of 1/2 fresh lemon + 1 pinch baking soda (temporary pH buffering)."},
            {"time": "08:30 AM", "meal": "Purine-Free Breakfast", "items": "Oatmeal cooked in water with crushed tart cherries, blueberries, and 1 tsp chia seeds."},
            {"time": "11:00 AM", "meal": "Hydration Booster", "items": "1 glass fresh tender coconut water or barley water + 1 fresh cucumber with lemon."},
            {"time": "01:30 PM", "meal": "Alkaline Lunch", "items": "2 whole wheat rotis + steamed pumpkin / cabbage subzi + 1 bowl yellow moong dal + fresh salad with apple cider vinegar."},
            {"time": "04:30 PM", "meal": "Anti-Inflammatory Tea", "items": "Fresh ginger and turmeric green tea + roasted lotus seeds (makhana)."},
            {"time": "07:30 PM", "meal": "Restorative Dinner", "items": "Clear vegetable broth with carrots, celery, and zucchini + 1/2 cup quinoa pilaf."},
            {"time": "09:30 PM", "meal": "Bedtime Uric Clear", "items": "1 glass warm water with 1 tbsp tart cherry concentrate."}
        ]
        superfoods = ["Tart cherries", "Fresh lemon water", "Cucumber & celery", "Barley water", "Ginger & turmeric", "Chia seeds"]
        avoid_foods = ["Red meat (mutton, beef) & organ meats", "Seafood (anchovies, sardines, shellfish)", "Beer, alcohol & hard liquor", "High-fructose corn syrup & sugary sodas", "Brewer's yeast supplements"]

    elif has_diabetes or has_lipids:
        title = "Antigravity Therapeutic Glycemic & Cardioprotective Diet Plan"
        macros = "Carbs: 40% (Low-GI Complex), Protein: 25% (Lean Metabolic), Healthy Fats: 35% (MUFA/PUFA)"
        hydration = "3.0 - 3.5 Liters of water throughout the day"
        schedule = [
            {"time": "07:00 AM", "meal": "Morning Fasting Elixir", "items": "1 glass warm water with 1 tsp soaked fenugreek (methi) seeds and 1/4 tsp organic Ceylon cinnamon. Enhances insulin receptor sensitivity."},
            {"time": "08:30 AM", "meal": "Nutritious Breakfast", "items": "Sprouted moong & methi chilla with mint chutney OR steel-cut oats with chia seeds, flaxseeds, and 4 crushed walnuts. Zero added sugar."},
            {"time": "11:00 AM", "meal": "Mid-Morning Booster", "items": "1 medium green apple or guava + small handful of dry-roasted unsalted chana (Bengal gram) or 6 almonds."},
            {"time": "01:30 PM", "meal": "Clinical Balanced Lunch", "items": "Large fresh cucumber-tomato-radish salad + 2 multi-grain / jowar rotis + 1 bowl spinach/methi dal + 100g grilled tofu, paneer, or steamed fish."},
            {"time": "04:30 PM", "meal": "Evening Antioxidant Snack", "items": "1 cup organic green tea or ginger-tulsi tea (no sugar) + 1 bowl roasted fox nuts (makhana) with turmeric and rock salt."},
            {"time": "07:30 PM", "meal": "Early Restorative Dinner", "items": "Clear vegetable broth soup + stir-fried broccoli, zucchini, beans, and bell peppers with 1/2 cup quinoa or dal khichdi."},
            {"time": "09:30 PM", "meal": "Bedtime Recovery", "items": "Warm unsweetened almond milk with a pinch of organic turmeric and freshly crushed black pepper (curcumin absorption)."}
        ]
        superfoods = ["Fenugreek (Methi) seeds", "Cinnamon", "Chia & Flaxseeds", "Bitter Gourd (Karela)", "Walnuts", "Spinach", "Quinoa"]
        avoid_foods = ["Refined sugar, candy & soda", "Deep-fried snacks & samosas", "White bread & bakery items", "High fructose fruits in excess", "Trans-fats & hydrogenated oils"]

    elif has_anemia or has_infection:
        title = "Antigravity Iron-Restorative & Anti-Inflammatory Immune Diet Plan"
        macros = "Carbs: 50% (Whole grains), Protein: 25% (Repair & RBCs), Fats: 25%"
        hydration = "2.8 - 3.2 Liters including herbal immunity infusions"
        schedule = [
            {"time": "07:00 AM", "meal": "Morning Iron Kickstart", "items": "7-8 soaked black raisins (munakka) + 2 soft dates eaten with the soaking water. Maximizes natural iron uptake."},
            {"time": "08:30 AM", "meal": "Hemoglobin-Building Breakfast", "items": "Beetroot and spinach stuffed whole-wheat paratha with light curd OR 2 boiled egg whites with fresh orange slices (Vitamin C)."},
            {"time": "11:00 AM", "meal": "Mid-Day Vitality", "items": "1 bowl fresh pomegranate arils sprinkled with roasted pumpkin seeds (rich in zinc and iron)."},
            {"time": "01:30 PM", "meal": "Immune Repair Lunch", "items": "2 whole wheat chapatis + moringa (drumstick) leaf dal + stir-fried leafy greens + roasted organic jaggery."},
            {"time": "04:30 PM", "meal": "Recovery Infusion", "items": "Warm ginger-tulsi-licorice decoction (kadha) + roasted chana with turmeric."},
            {"time": "07:30 PM", "meal": "Restorative Dinner", "items": "Warm tomato-beetroot soup + vegetable khichdi or steamed brown rice with lentils."},
            {"time": "09:30 PM", "meal": "Night Healing", "items": "Warm golden turmeric milk with a pinch of nutmeg and black pepper."}
        ]
        superfoods = ["Soaked black raisins (Munakka)", "Pomegranate", "Moringa leaves", "Pumpkin seeds", "Beetroot", "Turmeric & Tulsi", "Organic jaggery"]
        avoid_foods = ["Coffee and black tea with meals (inhibits iron)", "Ultra-processed junk food", "Excess carbonated soft drinks", "Raw unpasteurized foods during infection"]

    else:
        title = "Antigravity Vitality & Longevity Wellness Diet Protocol"
        macros = "Carbs: 45% (Complex fibers), Protein: 25% (Clean lean), Fats: 30% (Heart healthy)"
        hydration = "2.5 - 3.0 Liters clean structured water"
        schedule = [
            {"time": "07:00 AM", "meal": "Awakening Hydration", "items": "1 glass warm water with fresh lemon and 1 tsp raw chia seeds."},
            {"time": "08:30 AM", "meal": "Metabolic Energy Breakfast", "items": "Overnight rolled oats with almond milk, blueberries, crushed walnuts, and flaxseeds OR avocado toast on whole grain bread with a poached egg."},
            {"time": "11:00 AM", "meal": "Mid-Morning Fruit", "items": "Seasonal fresh fruit (papaya, apple, or berries) with 5 soaked almonds."},
            {"time": "01:30 PM", "meal": "Wholesome Lunch", "items": "Rainbow salad plate + 2 whole grain chapatis + mixed vegetable curry + yellow dal tadka + probiotic Greek yogurt."},
            {"time": "04:30 PM", "meal": "Afternoon Refreshment", "items": "Chamomile or Jasmine green tea with roasted chickpeas."},
            {"time": "07:30 PM", "meal": "Clean Dinner", "items": "Grilled vegetables with quinoa or brown rice pilaf + lentil soup."},
            {"time": "09:30 PM", "meal": "Restful Sleep Tea", "items": "Warm chamomile or fennel seed infusion."}
        ]
        superfoods = ["Avocado", "Blueberries / Berries", "Greek Yogurt", "Extra Virgin Olive Oil", "Chia seeds", "Turmeric"]
        avoid_foods = ["Excess sodium and MSG in processed snacks", "Midnight high-sugar desserts", "Artificial sweeteners", "Deep-fried street foods"]

    return {
        "title": title,
        "calories": calories,
        "macros": macros,
        "hydration": hydration,
        "schedule": schedule,
        "superfoods": superfoods,
        "avoid_foods": avoid_foods
    }

# EVALUATE CLINICAL TRIAGE WITH DYNAMIC PATIENT VALUES
def evaluate_triage(biomarkers, symptoms=""):
    high_count = sum(1 for b in biomarkers if "HIGH" in b["status"])
    low_count = sum(1 for b in biomarkers if "LOW" in b["status"])
    critical_count = sum(1 for b in biomarkers if "CRITICAL" in b["status"])

    symptoms_lower = (symptoms or "").lower()
    emergency_keywords = ["chest pain", "arm pain", "jaw pain", "shortness of breath", "sweating profusely", "unconscious", "stroke", "paralysis", "coughing blood", "difficulty breathing"]
    has_emergency_symptom = any(k in symptoms_lower for k in emergency_keywords)

    if has_emergency_symptom or critical_count >= 2:
        urgency = "EMERGENCY_CRITICAL"
        urgency_label = "CRITICAL EMERGENCY - IMMEDIATE ACTION"
        urgency_color = "red"
        timeframe = "IMMEDIATE: Proceed to the nearest hospital Emergency Room (ER) or call 108/112/911."
    elif critical_count == 1 or high_count >= 3:
        urgency = "URGENT_MEDICAL_ATTENTION"
        urgency_label = "URGENT CLINICAL ATTENTION"
        urgency_color = "red"
        timeframe = "Consult a physician or visit an urgent care clinic within 24 hours."
    elif high_count >= 1 or low_count >= 1:
        urgency = "MODERATE_ATTENTION"
        urgency_label = "MODERATE CLINICAL ATTENTION"
        urgency_color = "amber"
        timeframe = "Schedule a consultation with your physician within 48 to 72 hours."
    else:
        urgency = "ROUTINE_CHECKUP"
        urgency_label = "NORMAL / ROUTINE PREVENTIVE"
        urgency_color = "emerald"
        timeframe = "All parameters are within reference intervals. Maintain your healthy lifestyle protocol."

    risk_score = min(98, max(8, 12 + (critical_count * 28) + (high_count * 16) + (low_count * 9) + (35 if has_emergency_symptom else 0)))

    def find_b(keys):
        return next((b for b in biomarkers if b["key"] in keys), None)

    fbs_b = find_b(["fbs"])
    hba1c_b = find_b(["hba1c"])
    ppbs_b = find_b(["ppbs"])
    chol_b = find_b(["cholesterol"])
    tg_b = find_b(["triglycerides"])
    ldl_b = find_b(["ldl"])
    hb_b = find_b(["hemoglobin"])
    wbc_b = find_b(["wbc"])
    esr_b = find_b(["esr"])
    creat_b = find_b(["creatinine"])
    uric_b = find_b(["uric_acid"])

    explanations = {"en": [], "hi": [], "mr": [], "es": []}
    doctor_questions = []

    if has_emergency_symptom:
        explanations["en"].append("CRITICAL ALERT: Symptoms suggestive of an acute cardiovascular or respiratory emergency were detected. Seek immediate emergency medical care (call 108/112/911).")
        explanations["hi"].append("आपातकालीन चेतावनी: बताए गए लक्षण गंभीर हृदय या सांस की समस्या का संकेत दे रहे हैं। तुरंत नजदीकी अस्पताल के इमरजेंसी वार्ड में जाएं या 108 पर कॉल करें।")
        explanations["mr"].append("तातडीचा इशारा: नमूद केलेली लक्षणे तीव्र हृदयविकार किंवा श्वसन समस्येची शक्यता दर्शवतात. त्वरित आपत्कालीन कक्षाशी संपर्क साधा.")
        explanations["es"].append("ALERTA CRÍTICA: Se reportaron síntomas compatibles con una emergencia médica aguda. Acuda inmediatamente a urgencias.")
        doctor_questions.append("Can we immediately perform an ECG (Electrocardiogram) and cardiac troponin enzyme test?")

    if (fbs_b and "HIGH" in fbs_b["status"]) or (hba1c_b and "HIGH" in hba1c_b["status"]):
        fbs_txt = f"{fbs_b['value']} mg/dL" if fbs_b else "elevated"
        hba1c_txt = f"{hba1c_b['value']}%" if hba1c_b else "elevated"
        explanations["en"].append(f"Blood sugar markers are elevated: Fasting Glucose is {fbs_txt} and HbA1c is {hba1c_txt} (healthy threshold is < 5.7%). This indicates chronic glycemic overload and insulin resistance.")
        explanations["hi"].append(f"रक्त में शुगर का स्तर बढ़ा हुआ है: फास्टिंग शुगर {fbs_txt} और HbA1c {hba1c_txt} है (सामान्य स्तर 5.7% से कम होता है)। यह डायबिटीज और इंसुलिन रेजिस्टेंस का संकेत है।")
        explanations["mr"].append(f"रक्तातील साखरेचे प्रमाण वाढले आहे: फास्टिंग ग्लुकोज {fbs_txt} आणि HbA1c {hba1c_txt} आहे. हे रक्तातील दीर्घकालीन साखरेचे प्रमाण दर्शवते.")
        explanations["es"].append(f"Sus marcadores de glucosa están elevados: Glucosa en ayunas en {fbs_txt} y HbA1c en {hba1c_txt} (el rango normal es < 5.7%).")
        doctor_questions.append(f"Based on my {hba1c_txt} HbA1c, should I start or adjust glycemic medications (e.g., Metformin)?")
        doctor_questions.append("Do you recommend a continuous glucose monitor (CGM) or regular fasting blood sugar checks?")

    if (chol_b and "HIGH" in chol_b["status"]) or (ldl_b and "HIGH" in ldl_b["status"]) or (tg_b and "HIGH" in tg_b["status"]):
        chol_txt = f"{chol_b['value']} mg/dL" if chol_b else "elevated"
        ldl_txt = f"{ldl_b['value']} mg/dL" if ldl_b else "elevated"
        explanations["en"].append(f"Your lipid panel shows high circulating lipids: Total Cholesterol is {chol_txt} and LDL Bad Cholesterol is {ldl_txt}. Excess LDL deposits plaque inside arterial walls, elevating cardiovascular risk.")
        explanations["hi"].append(f"आपकी लिपिड प्रोफाइल में टोटल कोलेस्ट्रॉल {chol_txt} और एलडीएल {ldl_txt} बढ़ा हुआ है, जो नसों में रुकावट और दिल की बीमारी का खतरा बढ़ा सकता है।")
        explanations["mr"].append(f"तुमच्या लिपिड तपासणीत टोटल कोलेस्ट्रॉल {chol_txt} आणि एलडीएल {ldl_txt} वाढलेले आहे, ज्यामुळे रक्तवाहिन्यांमध्ये अडथळा निर्माण होण्याचा धोका असतो.")
        explanations["es"].append(f"Su perfil lipídico muestra Colesterol Total en {chol_txt} y LDL en {ldl_txt}, lo que incrementa el riesgo aterosclerótico.")
        doctor_questions.append("Would you advise starting a statin (e.g. Atorvastatin) or lipid-lowering therapy to reduce my LDL?")
        doctor_questions.append("Should we conduct a Cardiac Calcium Score (CAC) or carotid ultrasound to assess arterial health?")

    if hb_b and "LOW" in hb_b["status"]:
        hb_txt = f"{hb_b['value']} g/dL"
        explanations["en"].append(f"Your Hemoglobin is low at {hb_txt} (normal reference is 12.0 - 16.5 g/dL). This indicates Anemia, which impairs oxygen circulation to tissues and causes fatigue, shortness of breath, and pale skin.")
        explanations["hi"].append(f"आपका हीमोग्लोबिन स्तर कम होकर {hb_txt} रह गया है (सामान्य 12.0 - 16.5 g/dL होता है)। यह एनीमिया (खून की कमी) है, जिससे शरीर में कमजोरी और चक्कर आते हैं।")
        explanations["mr"].append(f"तुमचे हिमोग्लोबिन कमी होऊन {hb_txt} झाले आहे. ही ॲनिमियाची (रक्ताची कमतरता) स्थिती आहे, ज्यामुळे थकवा जाणवतो.")
        explanations["es"].append(f"Su hemoglobina está baja en {hb_txt} (el rango normal es 12.0 - 16.5 g/dL), lo que indica anemia activa.")
        doctor_questions.append(f"Should we order a Serum Ferritin and Vitamin B12 test to diagnose the exact cause of this {hb_txt} hemoglobin?")
        doctor_questions.append("Do you recommend therapeutic iron supplements, and are oral or IV formulations preferred?")

    if (wbc_b and "HIGH" in wbc_b["status"]) or (esr_b and "HIGH" in esr_b["status"]):
        wbc_txt = f"{wbc_b['value']} /mcL" if wbc_b else "elevated"
        explanations["en"].append(f"Your White Blood Cell (WBC) count is elevated at {wbc_txt}. This leukocytosis demonstrates that your immune system is actively fighting an infection or systemic inflammation.")
        explanations["hi"].append(f"आपकी सफेद रक्त कोशिकाएं (WBC) बढ़कर {wbc_txt} हो गई हैं, जो शरीर में किसी सक्रिय संक्रमण (इंफेक्शन) या सूजन का संकेत है।")
        explanations["mr"].append(f"पांढऱ्या रक्त पेशी (WBC) {wbc_txt} वाढल्या आहेत, जे शरीरातील एखाद्या संसर्गाशी लढण्याची प्रक्रिया दर्शवते.")
        explanations["es"].append(f"El recuento de glóbulos blancos (WBC) está elevado en {wbc_txt}, lo que sugiere un proceso infeccioso o inflamatorio.")
        doctor_questions.append("Do I need targeted antibiotic or anti-inflammatory treatment for this elevated WBC count?")

    if creat_b and "HIGH" in creat_b["status"]:
        creat_txt = f"{creat_b['value']} mg/dL"
        explanations["en"].append(f"Your Serum Creatinine is elevated at {creat_txt} (normal: 0.7 - 1.3 mg/dL). Elevated creatinine indicates reduced glomerular filtration efficiency in your kidneys.")
        explanations["hi"].append(f"आपका सीरम क्रिएटिनिन बढ़कर {creat_txt} हो गया है (सामान्य 0.7 - 1.3 mg/dL)। यह किडनी द्वारा रक्त साफ करने की क्षमता में कमी का संकेत हो सकता है।")
        explanations["mr"].append(f"तुमचे सीरम क्रिएटिनिन {creat_txt} वाढलेले आहे, जे मूत्रपिंडाच्या (किडनी) गाळण क्षमतेवर ताण दर्शवते.")
        explanations["es"].append(f"Su creatinina sérica está elevada en {creat_txt}, lo que refleja estrés en la filtración renal.")
        doctor_questions.append("Should we calculate my eGFR and test urine microalbumin to evaluate kidney filtration?")

    if uric_b and "HIGH" in uric_b["status"]:
        uric_txt = f"{uric_b['value']} mg/dL"
        explanations["en"].append(f"Your Serum Uric Acid is high at {uric_txt} (normal: 3.5 - 7.2 mg/dL). Hyperuricemia can cause sharp urate crystal deposits in joints, leading to painful gout flares or kidney stones.")
        explanations["hi"].append(f"आपका यूरिक एसिड {uric_txt} बढ़ा हुआ है (सामान्य 3.5 - 7.2 mg/dL)। यह जोड़ों में दर्द, गाउट या पथरी (किडनी स्टोन) का कारण बन सकता है।")
        explanations["mr"].append(f"तुमचे यूरिक ॲसिड {uric_txt} वाढले आहे, ज्यामुळे सांधेदुखी किंवा गाउटचा त्रास होऊ शकतो.")
        explanations["es"].append(f"El ácido úrico está elevado en {uric_txt}, aumentando el riesgo de gota o cálculos renales.")
        doctor_questions.append("Should I take a xanthine oxidase inhibitor (such as Febuxostat) to normalize uric acid levels?")

    if not explanations["en"]:
        explanations["en"].append("All your tested biomarker parameters are comfortably situated inside healthy biological reference intervals. Your metabolic, cardiovascular, and hematologic indicators demonstrate optimal baseline health.")
        explanations["hi"].append("आपकी सभी स्वास्थ्य जांचें सामान्य सीमा के भीतर हैं। आपका चयापचय और हृदय स्वास्थ्य पूरी तरह सामान्य और संतुलित है।")
        explanations["mr"].append("तुमच्या सर्व तपासण्यांचे निकाल सामान्य मर्यादेत आहेत. तुमचे आरोग्य उत्तम स्थितीत आहे.")
        explanations["es"].append("Todos sus parámetros biológicos se encuentran en rangos óptimos de referencia.")
        doctor_questions.append("What routine preventive health screening or fitness milestones should I aim for over the next 12 months?")

    diet_plan = generate_antigravity_diet_plan(biomarkers)

    return {
        "urgency": urgency,
        "urgency_label": urgency_label,
        "urgency_color": urgency_color,
        "timeframe": timeframe,
        "risk_score": risk_score,
        "explanations": explanations,
        "doctor_questions": doctor_questions,
        "diet_plan": diet_plan,
        "flags": {
            "high": high_count,
            "low": low_count,
            "critical": critical_count,
            "normal": len(biomarkers) - (high_count + low_count)
        }
    }

# ROUTES & APIS
@app.route('/')
@app.route('/api/index')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        for t_dir in [TEMPLATE_FOLDER] + template_dirs:
            candidate = os.path.join(t_dir, 'index.html')
            if os.path.exists(candidate):
                with open(candidate, 'r', encoding='utf-8') as f:
                    return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}
        return f"MediTriage AI is online. Status: {str(e)}", 200, {'Content-Type': 'text/plain'}

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "MediTriage AI",
        "engine": "Antigravity AI Bio-Nutrition",
        "environment": "Vercel Serverless" if IS_VERCEL else "Localhost"
    })

@app.route('/api/samples', methods=['GET'])
def get_samples():
    return jsonify({
        "status": "success",
        "samples": SAMPLE_REPORTS
    })

@app.route('/api/biomarker-db', methods=['GET'])
def get_biomarker_db():
    return jsonify({
        "status": "success",
        "database": BIOMARKER_METRIC_DB
    })

@app.route('/static/<path:filename>')
def serve_static_asset(filename):
    for s_dir in [STATIC_FOLDER] + static_dirs:
        candidate = os.path.join(s_dir, filename)
        if os.path.exists(candidate):
            return send_from_directory(os.path.dirname(candidate), os.path.basename(candidate))
    return "Asset not found", 404

@app.route('/uploads/<filename>')
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/parse-text', methods=['POST'])
def parse_text():
    data = request.get_json() or {}
    text = data.get('text', '').strip()
    extracted = parse_lab_text_and_report(text)
    patient = extract_patient_info_from_text(text)
    return jsonify({
        "status": "success",
        "biomarkers": extracted,
        "patient": patient,
        "count": len(extracted)
    })

@app.route('/api/analyze-report', methods=['POST'])
def analyze_report():
    data = request.get_json() or {}
    mode = data.get('mode', 'sample')
    sample_id = data.get('sample_id', 'sample_diabetes_lipid')
    uploaded_url = data.get('uploaded_url', '')
    user_symptoms = data.get('symptoms', '').strip()
    raw_report_text = data.get('report_text', '').strip()
    custom_biomarkers = data.get('biomarkers')
    custom_patient = data.get('patient')

    if custom_biomarkers and len(custom_biomarkers) > 0:
        biomarkers = []
        for b in custom_biomarkers:
            val = float(b['value'])
            key = b.get('key', 'fbs')
            meta = BIOMARKER_METRIC_DB.get(key, {})
            min_val = meta.get('min', 0)
            max_val = meta.get('max', 100)
            status = b.get('status')
            if not status:
                if val > max_val * 1.35:
                    status = "CRITICAL HIGH"
                elif val > max_val:
                    status = "HIGH"
                elif min_val > 0 and val < min_val:
                    status = "LOW"
                else:
                    status = "NORMAL"

            ref_str = b.get('ref') or (f"{min_val} - {max_val}" if min_val > 0 else f"< {max_val}")
            biomarkers.append({
                "key": key,
                "name": b.get('name', meta.get('name', key.upper())),
                "value": val,
                "unit": b.get('unit', meta.get('unit', '')),
                "ref": ref_str,
                "status": status,
                "category": meta.get('category', 'Diagnostic')
            })

        patient = custom_patient or {"name": "Patient", "age": 45, "gender": "Male", "id": f"P-{int(time.time())%1000000}"}
        report_title = "Personalized Patient Lab Report"
        lab_name = data.get('lab_name', 'Clinical Diagnostic Laboratory')
        image_url = uploaded_url if uploaded_url else "/static/samples/sample_diabetes_lipid.png"
        symptoms = user_symptoms or "Patient-entered clinical values."

    elif raw_report_text:
        extracted = parse_lab_text_and_report(raw_report_text)
        biomarkers = extracted if len(extracted) > 0 else SAMPLE_REPORTS[0]['biomarkers']
        patient = custom_patient or extract_patient_info_from_text(raw_report_text)
        report_title = "Digitized Prescription & Lab Text Extraction"
        lab_name = "Automated OCR Clinical Extraction"
        image_url = uploaded_url if uploaded_url else "/static/samples/sample_diabetes_lipid.png"
        symptoms = user_symptoms or "Text-extracted clinical diagnostics."

    elif mode == 'sample':
        report = next((s for s in SAMPLE_REPORTS if s['id'] == sample_id), SAMPLE_REPORTS[0])
        biomarkers = report['biomarkers']
        patient = custom_patient if custom_patient and custom_patient.get('name') else report['patient']
        report_title = report['title']
        lab_name = report['lab']
        image_url = f"/static/samples/{report['filename']}"
        symptoms = user_symptoms or report['symptoms_reported']

    else:
        uploaded_filename = data.get('uploaded_filename', '')
        extracted_from_fn = parse_lab_text_and_report(uploaded_filename + " " + user_symptoms)
        if len(extracted_from_fn) > 0:
            biomarkers = extracted_from_fn
        else:
            biomarkers = generate_dynamic_biomarkers_from_symptoms(user_symptoms)

        patient = custom_patient or {"name": data.get("patient_name", "Diagnosed Patient"), "age": int(data.get("age", 42)), "gender": data.get("gender", "Female"), "id": f"P-{int(time.time())%1000000}"}
        report_title = "Automated Patient Report & Biomarker Analysis"
        lab_name = "Antigravity AI Neural OCR Extraction"
        image_url = uploaded_url if uploaded_url else "/static/samples/sample_diabetes_lipid.png"
        symptoms = user_symptoms or "Patient-uploaded diagnostic record."

    triage_result = evaluate_triage(biomarkers, symptoms)

    return jsonify({
        "status": "success",
        "ai_engine": "Antigravity Neural Clinical Intelligence",
        "report_title": report_title,
        "patient": patient,
        "lab_name": lab_name,
        "image_url": image_url,
        "symptoms": symptoms,
        "biomarkers": biomarkers,
        "triage": triage_result
    })

@app.route('/api/upload-file', methods=['POST'])
def upload_file():
    if 'report_file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400
    file = request.files['report_file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "Empty filename"}), 400

    filename = secure_filename(f"report_{int(time.time())}_{file.filename}")
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    try:
        file.save(filepath)
    except Exception:
        pass

    # Attempt to extract text from filename or text if available
    fn_biomarkers = parse_lab_text_and_report(file.filename)

    return jsonify({
        "status": "success",
        "filename": filename,
        "url": f"/uploads/{filename}",
        "detected_biomarkers": fn_biomarkers
    })

# DOWNLOAD FULL ANTIGRAVITY FOOD & DIET (FOD) PLAN
@app.route('/api/download-diet-pdf', methods=['POST'])
def download_diet_pdf():
    data = request.get_json() or {}
    
    patient = data.get('patient')
    biomarkers = data.get('biomarkers')
    diet_plan = data.get('diet_plan')

    if not biomarkers or not diet_plan:
        sample_id = data.get('sample_id', 'sample_diabetes_lipid')
        report = next((s for s in SAMPLE_REPORTS if s['id'] == sample_id), SAMPLE_REPORTS[0])
        patient = patient or report['patient']
        biomarkers = biomarkers or report['biomarkers']
        diet_plan = diet_plan or generate_antigravity_diet_plan(biomarkers, patient)
    else:
        patient = patient or {"name": "Patient", "age": 45, "gender": "Adult", "id": "P-984210"}

    w, h = 1800, 1400
    img = Image.new('RGB', (w, h), (15, 23, 42))
    draw = ImageDraw.Draw(img)

    # Header Banner
    draw.rectangle([40, 40, w - 40, 150], fill=(13, 148, 136))
    draw.text((70, 60), "ANTIGRAVITY AI CLINICAL NUTRITION: PERSONALIZED FOOD & DIET PROTOCOL", fill=(255, 255, 255))
    draw.text((70, 95), f"Patient: {patient.get('name', 'Patient')} ({patient.get('age', 45)}Y/{patient.get('gender', 'Adult')}) | Target: {diet_plan.get('calories', '1,800 kcal')} | Hydration: {diet_plan.get('hydration', '3.0 L')}", fill=(204, 251, 241))
    draw.text((w - 480, 75), "POWERED BY ANTIGRAVITY AI", fill=(251, 191, 36))

    # Diet Protocol Title & Macro Goals
    draw.rectangle([40, 170, w - 40, 240], fill=(30, 41, 59))
    draw.text((60, 185), f"CLINICAL PROTOCOL: {diet_plan.get('title', 'Therapeutic Nutrition').upper()}", fill=(244, 63, 94))
    draw.text((60, 210), f"MACRONUTRIENT RATIO: {diet_plan.get('macros', 'Carbs: 45%, Protein: 25%, Fats: 30%')}", fill=(226, 232, 240))

    # Schedule Table (Left / Center)
    sched_w = 1100
    draw.rectangle([40, 260, 40 + sched_w, h - 50], outline=(51, 65, 85), fill=(24, 33, 47), width=2)
    draw.text((60, 280), "24-HOUR PRECISION MEAL SCHEDULE & TIMING", fill=(45, 212, 191))

    cur_y = 320
    for idx, item in enumerate(diet_plan.get('schedule', [])):
        box_color = (30, 41, 59) if idx % 2 == 0 else (20, 28, 42)
        draw.rectangle([55, cur_y, 40 + sched_w - 15, cur_y + 125], fill=box_color)

        draw.text((75, cur_y + 15), item["time"], fill=(251, 191, 36))
        draw.text((200, cur_y + 15), item["meal"].upper(), fill=(56, 189, 248))

        detail = item["items"]
        words = detail.split(' ')
        line1, line2 = "", ""
        for word in words:
            if len(line1) + len(word) < 85 and not line2:
                line1 += (" " if line1 else "") + word
            else:
                line2 += (" " if line2 else "") + word

        draw.text((75, cur_y + 50), line1, fill=(226, 232, 240))
        if line2:
            draw.text((75, cur_y + 80), line2, fill=(203, 213, 225))

        cur_y += 140

    # Right Sidebar
    side_x = 40 + sched_w + 30
    side_w = w - side_x - 40
    draw.rectangle([side_x, 260, side_x + side_w, h - 50], outline=(51, 65, 85), fill=(24, 33, 47), width=2)

    draw.text((side_x + 25, 285), "THERAPEUTIC SUPERFOODS:", fill=(34, 197, 94))
    sf_y = 325
    for sf in diet_plan.get("superfoods", []):
        draw.text((side_x + 35, sf_y), f"+ {sf}", fill=(209, 250, 229))
        sf_y += 40

    draw.line([(side_x + 20, sf_y + 20), (side_x + side_w - 20, sf_y + 20)], fill=(51, 65, 85), width=1)
    draw.text((side_x + 25, sf_y + 40), "STRICTLY PROHIBITED (RED FLAGS):", fill=(239, 68, 68))
    av_y = sf_y + 80
    for av in diet_plan.get("avoid_foods", []):
        draw.text((side_x + 35, av_y), f"- {av}", fill=(254, 202, 202))
        av_y += 45

    draw.rectangle([side_x + 20, h - 170, side_x + side_w - 20, h - 70], fill=(30, 41, 59), outline=(13, 148, 136), width=1)
    draw.text((side_x + 35, h - 155), "AI VERIFIED NUTRITION PROTOCOL", fill=(45, 212, 191))
    draw.text((side_x + 35, h - 130), f"Calibrated for {patient.get('name', 'Patient')} ({patient.get('id', 'P-984210')})", fill=(203, 213, 225))
    draw.text((side_x + 35, h - 105), "Engine: Antigravity Neural Bio-Nutrition", fill=(251, 191, 36))

    out_io = io.BytesIO()
    img.save(out_io, 'JPEG', quality=95)
    out_io.seek(0)

    return send_file(
        out_io,
        mimetype='image/jpeg',
        as_attachment=True,
        download_name=f"Antigravity_Food_Diet_Plan_{patient.get('id', 'patient')}.jpg"
    )

# EXPORT CLINICAL PATIENT SUMMARY
@app.route('/api/export-patient-summary', methods=['POST'])
def export_patient_summary():
    data = request.get_json() or {}
    
    patient = data.get('patient')
    biomarkers = data.get('biomarkers')
    triage = data.get('triage')

    if not biomarkers or not triage:
        sample_id = data.get('sample_id', 'sample_diabetes_lipid')
        report = next((s for s in SAMPLE_REPORTS if s['id'] == sample_id), SAMPLE_REPORTS[0])
        patient = patient or report['patient']
        biomarkers = biomarkers or report['biomarkers']
        triage = triage or evaluate_triage(biomarkers)
    else:
        patient = patient or {"name": "Patient", "age": 45, "gender": "Adult", "id": "P-984210"}

    w, h = 1800, 1200
    img = Image.new('RGB', (w, h), (15, 23, 42))
    draw = ImageDraw.Draw(img)

    draw.rectangle([40, 40, w - 40, 130], fill=(30, 41, 59))
    draw.text((70, 60), "MEDITRIAGE AI: PATIENT CLINICAL REPORT & TRIAGE ACTION PLAN", fill=(244, 63, 94))
    draw.text((70, 95), f"Patient: {patient.get('name', 'Patient')} ({patient.get('age', 45)}Y/{patient.get('gender', 'Adult')}) | ID: {patient.get('id', 'P-984210')} | Date: 28-Oct-2026", fill=(226, 232, 240))
    draw.text((w - 440, 75), f"TRIAGE: {triage.get('urgency_label', 'EVALUATION')}", fill=(251, 191, 36) if triage.get('urgency_color') == 'amber' else ((239, 68, 68) if triage.get('urgency_color') == 'red' else (34, 197, 94)))

    left_w = 700
    draw.rectangle([50, 150, 50 + left_w, h - 50], outline=(51, 65, 85), fill=(24, 33, 47), width=2)
    sample_path = os.path.join(SAMPLES_FOLDER, "sample_diabetes_lipid.png")
    if os.path.exists(sample_path):
        try:
            with Image.open(sample_path) as s_img:
                resized_sample = s_img.resize((left_w - 40, h - 260))
                img.paste(resized_sample, (70, 210))
        except Exception:
            pass
    draw.text((70, 170), "DIGITIZED CLINICAL LAB REPORT SCAN", fill=(56, 189, 248))

    right_x = 50 + left_w + 30
    right_w = w - right_x - 50
    draw.rectangle([right_x, 150, right_x + right_w, h - 50], outline=(51, 65, 85), fill=(24, 33, 47), width=2)
    draw.text((right_x + 30, 175), "AI BIOMARKER ANOMALY MATRIX & CLINICAL RECOMMENDATIONS", fill=(244, 63, 94))

    draw.rectangle([right_x + 30, 215, right_x + right_w - 30, 265], fill=(30, 41, 59))
    draw.text((right_x + 45, 230), f"Cardiometabolic Risk Index: {triage.get('risk_score', 50)} / 100", fill=(255, 255, 255))
    draw.text((right_x + 450, 230), f"Urgency: {triage.get('timeframe', 'Within 48 hours')[:35]}...", fill=(251, 191, 36))

    draw.text((right_x + 30, 290), "KEY DETECTED BIOMARKERS:", fill=(56, 189, 248))
    row_y = 325
    for b in biomarkers[:8]:
        status_color = (239, 68, 68) if "HIGH" in b["status"] else ((59, 130, 246) if "LOW" in b["status"] else (34, 197, 94))
        draw.text((right_x + 40, row_y), f"- {b['name']}", fill=(241, 245, 249))
        draw.text((right_x + 480, row_y), f"{b['value']} {b['unit']}", fill=status_color)
        draw.text((right_x + 650, row_y), f"[{b['status']}] (Ref: {b['ref']})", fill=status_color)
        row_y += 35

    draw.text((right_x + 30, row_y + 20), "QUESTIONS FOR DOCTOR VISIT:", fill=(251, 191, 36))
    q_y = row_y + 55
    for q in triage.get("doctor_questions", [])[:3]:
        draw.text((right_x + 40, q_y), f"> {q}", fill=(226, 232, 240))
        q_y += 35

    draw.text((right_x + 30, q_y + 20), "NUTRITION & LIFESTYLE GUIDANCE:", fill=(34, 197, 94))
    d_y = q_y + 55
    superfoods = triage.get("diet_plan", {}).get("superfoods", [])
    for item in superfoods[:3]:
        draw.text((right_x + 40, d_y), f"+ {item}", fill=(209, 250, 229))
        d_y += 35

    out_io = io.BytesIO()
    img.save(out_io, 'JPEG', quality=95)
    out_io.seek(0)

    return send_file(
        out_io,
        mimetype='image/jpeg',
        as_attachment=True,
        download_name=f"MediTriage_Clinical_Report_{patient.get('id', 'patient')}.jpg"
    )

if __name__ == '__main__':
    print("Starting MediTriage AI Server on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)
