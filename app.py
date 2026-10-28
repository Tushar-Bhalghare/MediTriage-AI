import os
import io
import time
import json
from flask import Flask, request, jsonify, render_template, send_from_directory, send_file
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
SAMPLES_FOLDER = os.path.join(STATIC_FOLDER, 'samples')

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=STATIC_FOLDER
)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SAMPLES_FOLDER, exist_ok=True)

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
    "esr": {"name": "ESR (Erythrocyte Sedimentation Rate)", "unit": "mm/hr", "min": 0.0, "max": 20.0, "category": "Inflammatory Marker"}
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
            {"key": "neutrophils", "name": "Neutrophils", "value": 78, "unit": "%", "ref": "40 - 70", "status": "HIGH"},
            {"key": "lymphocytes", "name": "Lymphocytes", "value": 18, "unit": "%", "ref": "20 - 40", "status": "LOW"},
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

# ANTIGRAVITY AI FULL FOOD & DIET (FOD) ENGINE
def generate_antigravity_diet_plan(biomarkers):
    has_diabetes = any(b["key"] in ["fbs", "hba1c", "ppbs"] and "HIGH" in b["status"] for b in biomarkers)
    has_lipids = any(b["key"] in ["cholesterol", "ldl", "triglycerides"] and "HIGH" in b["status"] for b in biomarkers)
    has_anemia = any(b["key"] == "hemoglobin" and "LOW" in b["status"] for b in biomarkers)
    has_infection = any(b["key"] in ["wbc", "esr"] and "HIGH" in b["status"] for b in biomarkers)

    if has_diabetes or has_lipids:
        title = "Antigravity Therapeutic Glycemic & Cardioprotective Diet Plan"
        calories = "1,650 kcal / day"
        macros = "Carbs: 40% (Complex), Protein: 25% (Lean), Healthy Fats: 35% (MUFA/PUFA)"
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
        avoid_foods = ["Refined sugar, candy & soda", "Deep-fried snacks & samosas", "White bread & bakery items", "High fructose fruits (chiku, mango) in excess", "Trans-fats & hydrogenated oils"]
    
    elif has_anemia or has_infection:
        title = "Antigravity Iron-Restorative & Anti-Inflammatory Immune Diet Plan"
        calories = "1,850 kcal / day"
        macros = "Carbs: 50% (Whole grains), Protein: 25% (Repair & RBCs), Fats: 25%"
        hydration = "2.8 - 3.0 Liters including herbal immunity infusions"

        schedule = [
            {"time": "07:00 AM", "meal": "Morning Iron Kickstart", "items": "7-8 soaked black raisins (munakka) + 2 soft dates eaten with the soaking water. Maximizes natural iron uptake."},
            {"time": "08:30 AM", "meal": "Hemoglobin-Building Breakfast", "items": "Beetroot and spinach stuffed whole-wheat paratha with light curd OR 2 boiled egg whites with fresh orange slices (Vitamin C)."},
            {"time": "11:00 AM", "meal": "Mid-Morning Vitamin C Boost", "items": "Fresh amla (Indian gooseberry) shot or 1 cup fresh pomegranate pearls with lemon juice squeeze."},
            {"time": "01:30 PM", "meal": "Immune Nourishing Lunch", "items": "1.5 cup brown rice / rotis + 1 bowl moringa (drumstick) lentil dal + iron-packed cooked mustard/bathua greens + squeeze of fresh lemon."},
            {"time": "04:30 PM", "meal": "Evening Vitality Snack", "items": "1 glass fresh lemon water or coconut water + small handful of roasted pumpkin and sunflower seeds (rich in zinc & iron)."},
            {"time": "07:30 PM", "meal": "Light Healing Dinner", "items": "Warm lentil & vegetable soup + steamed vegetables with soya chunks / paneer bhurji + small beetroot salad."},
            {"time": "09:30 PM", "meal": "Bedtime Immunity Elixir", "items": "Warm golden milk (haldi doodh) with a pinch of nutmeg to promote restorative cellular sleep."}
        ]

        superfoods = ["Moringa (Drumstick) leaves", "Amla (Gooseberry)", "Pomegranate", "Beetroot", "Black Raisins", "Pumpkin seeds", "Dates"]
        avoid_foods = ["Drinking tea/coffee within 1 hour of meals (tannins block iron absorption)", "Calcium supplements taken simultaneously with iron", "Raw cold foods during active fever", "Carbonated sugary sodas"]
    
    else:
        title = "Antigravity Optimal Longevity & Cellular Wellness Protocol"
        calories = "2,000 kcal / day"
        macros = "Balanced Mediterranean: 45% Complex Carbs, 25% Protein, 30% Healthy Fats"
        hydration = "2.5 - 3.0 Liters of water daily"

        schedule = [
            {"time": "07:00 AM", "meal": "Hydration & Gut Balance", "items": "Lukewarm water with fresh lemon juice and 1 tsp chia seeds."},
            {"time": "08:30 AM", "meal": "Energy-Dense Breakfast", "items": "Avocado or peanut butter toast on multi-seed bread with poached eggs or overnight oats with berries."},
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

# EVALUATE CLINICAL TRIAGE
def evaluate_triage(biomarkers, symptoms=""):
    high_count = sum(1 for b in biomarkers if "HIGH" in b["status"])
    low_count = sum(1 for b in biomarkers if "LOW" in b["status"])
    critical_count = sum(1 for b in biomarkers if "CRITICAL" in b["status"])

    if critical_count > 0 or high_count >= 4:
        urgency = "CRITICAL_URGENT"
        urgency_label = "URGENT MEDICAL ATTENTION"
        urgency_color = "red"
        timeframe = "Consult a physician or visit an urgent care clinic within 24 hours."
    elif high_count >= 2 or low_count >= 2:
        urgency = "MODERATE_ATTENTION"
        urgency_label = "MODERATE CLINICAL ATTENTION"
        urgency_color = "amber"
        timeframe = "Schedule a consultation with your general physician within 48 to 72 hours."
    else:
        urgency = "ROUTINE_CHECKUP"
        urgency_label = "NORMAL / ROUTINE PREVENTIVE"
        urgency_color = "emerald"
        timeframe = "Parameters are optimal. Maintain healthy lifestyle; repeat annual routine checkup."

    risk_score = min(96, max(12, (high_count * 18) + (critical_count * 25) + (low_count * 10) + 12))

    has_diabetes_risk = any(b["key"] in ["fbs", "hba1c", "ppbs"] and "HIGH" in b["status"] for b in biomarkers)
    has_lipid_risk = any(b["key"] in ["cholesterol", "ldl", "triglycerides"] and "HIGH" in b["status"] for b in biomarkers)
    has_anemia_risk = any(b["key"] == "hemoglobin" and "LOW" in b["status"] for b in biomarkers)
    has_infection_risk = any(b["key"] in ["wbc", "esr", "neutrophils"] and "HIGH" in b["status"] for b in biomarkers)

    explanations = {"en": [], "hi": [], "mr": [], "es": []}

    if has_diabetes_risk:
        explanations["en"].append("Your blood sugar markers (Fasting Glucose and HbA1c) are significantly above the healthy threshold. An HbA1c above 6.5% indicates chronic elevation of sugar in your bloodstream, consistent with Type 2 Diabetes.")
        explanations["hi"].append("आपके रक्त में शुगर (FBS और HbA1c) का स्तर सामान्य सीमा से काफी अधिक है। 6.5% से अधिक HbA1c पिछले 3 महीनों के उच्च शुगर स्तर को दर्शाता है, जो टाइप 2 डायबिटीज का संकेत हो सकता है।")
        explanations["mr"].append("तुमच्या रक्तातील साखरेचे प्रमाण (FBS आणि HbA1c) सामान्य प्रमाणापेक्षा खूप जास्त आहे. HbA1c 6.5% पेक्षा जास्त असणे मागील 3 महिन्यांतील उच्च साखरेचे प्रमाण दर्शवते, जे मधुमेहाचे लक्षण आहे.")
        explanations["es"].append("Sus niveles de glucosa en sangre (glucosa en ayunas y HbA1c) están significativamente elevados, lo que sugiere un control glucémico deficiente compatible con Diabetes Tipo 2.")

    if has_lipid_risk:
        explanations["en"].append("Your lipid panel shows elevated Total Cholesterol, LDL ('Bad') Cholesterol, and Triglycerides. High LDL deposits plaque on arterial walls, increasing cardiovascular risk.")
        explanations["hi"].append("आपकी लिपिड प्रोफाइल में बैड कोलेस्ट्रॉल (LDL) और ट्राइग्लिसराइड्स बढ़े हुए हैं। यह नसों में रुकावट पैदा कर दिल की बीमारी का खतरा बढ़ा सकता है।")
        explanations["mr"].append("तुमच्या लिपिड प्रोफाईलमध्ये बॅड कोलेस्ट्रॉल (LDL) आणि ट्रायग्लिसराइड्स वाढलेले आहेत. यामुळे रक्तवाहिन्यांमध्ये अडथळा निर्माण होऊन हृदयाचे आजार होण्याचा धोका संभवतो.")
        explanations["es"].append("Su perfil lipídico muestra niveles elevados de Colesterol Total, LDL y Triglicéridos, lo que aumenta el riesgo cardiovascular.")

    if has_anemia_risk:
        explanations["en"].append("Your Hemoglobin count is noticeably below reference range (9.2 g/dL), which indicates moderate Anemia. This reduces oxygen delivery to your body, explaining fatigue and dizziness.")
        explanations["hi"].append("आपका हीमोग्लोबिन स्तर सामान्य से कम (9.2 g/dL) है, जो एनीमिया (रक्त की कमी) का संकेत है। इससे शरीर में थकान और चक्कर आना स्वाभाविक है।")
        explanations["mr"].append("तुमचे हिमोग्लोबिन सामान्य प्रमाणापेक्षा कमी (9.2 g/dL) आहे, जे ॲनिमियाचे (रक्ताची कमतरता) लक्षण आहे. यामुळे थकवा आणि चक्कर येणे होऊ शकते.")
        explanations["es"].append("Su nivel de hemoglobina está bajo (9.2 g/dL), lo que indica anemia moderada responsable del cansancio y debilidad.")

    if has_infection_risk:
        explanations["en"].append("Elevated White Blood Cell (WBC) count and ESR suggest an active immune response to an infection or inflammatory condition currently in your body.")
        explanations["hi"].append("सफेद रक्त कोशिकाएं (WBC) और ESR बढ़े हुए हैं, जो शरीर में किसी सक्रिय संक्रमण (इंफेक्शन) या सूजन से लड़ने का संकेत देते हैं।")
        explanations["mr"].append("पांढऱ्या रक्त पेशी (WBC) आणि ESR वाढलेले आहेत, जे शरीरातील एखाद्या संसर्गाशी (इन्फेक्शन) किंवा जळजळीशी लढत असल्याचे दर्शवतात.")
        explanations["es"].append("El recuento elevado de glóbulos blancos (WBC) y la velocidad de sedimentación (ESR) indican una infección o proceso inflamatorio activo.")

    if not has_diabetes_risk and not has_lipid_risk and not has_anemia_risk and not has_infection_risk:
        explanations["en"].append("All your major blood parameters are sitting comfortably inside their optimal biological reference intervals. Your metabolic, renal, and hematologic functions are healthy.")
        explanations["hi"].append("आपकी सभी मुख्य रक्त जांचें सामान्य सीमा के भीतर हैं। आपकी मेटाबॉलिक और किडनी की कार्यप्रणाली पूरी तरह स्वस्थ है।")
        explanations["mr"].append("तुमच्या सर्व रक्त चाचण्या सामान्य मर्यादेत आहेत. तुमचे आरोग्य आणि चयापचय कार्य उत्तम स्थितीत आहे.")
        explanations["es"].append("Todos sus parámetros sanguíneos se encuentran dentro de los rangos biológicos de referencia normales.")

    doctor_questions = []
    if has_diabetes_risk:
        doctor_questions.append("Should I begin or adjust glycemic control medications (such as Metformin) based on my 8.4% HbA1c?")
        doctor_questions.append("Do I need a continuous glucose monitoring (CGM) or home glucometer check regimen?")
    if has_lipid_risk:
        doctor_questions.append("Would you recommend starting a statin (e.g., Atorvastatin) to lower my LDL cholesterol below 100 mg/dL?")
        doctor_questions.append("Should we perform a Cardiac Calcium Scoring or Carotid Doppler test to check arterial plaque?")
    if has_anemia_risk:
        doctor_questions.append("Could this anemia be iron deficiency or B12/folate deficiency? Should we test Serum Ferritin?")
    if has_infection_risk:
        doctor_questions.append("Given my elevated WBC and ESR, should we test for a specific bacterial/viral focus (e.g., urine culture, chest X-ray)?")
    if not doctor_questions:
        doctor_questions.append("Are there any preventive dietary or fitness benchmarks I should adopt to maintain these numbers?")
        doctor_questions.append("When should I schedule my next routine annual blood panel?")

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/samples', methods=['GET'])
def get_samples():
    return jsonify({
        "status": "success",
        "samples": SAMPLE_REPORTS
    })

@app.route('/static/samples/<filename>')
def serve_sample(filename):
    return send_from_directory(SAMPLES_FOLDER, filename)

@app.route('/uploads/<filename>')
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/analyze-report', methods=['POST'])
def analyze_report():
    data = request.get_json() or {}
    mode = data.get('mode', 'sample')
    sample_id = data.get('sample_id', 'sample_diabetes_lipid')
    uploaded_url = data.get('uploaded_url', '')
    user_symptoms = data.get('symptoms', '').strip()

    if mode == 'sample':
        report = next((s for s in SAMPLE_REPORTS if s['id'] == sample_id), SAMPLE_REPORTS[0])
        biomarkers = report['biomarkers']
        patient = report['patient']
        report_title = report['title']
        lab_name = report['lab']
        image_url = f"/static/samples/{report['filename']}"
        symptoms = user_symptoms or report['symptoms_reported']
    else:
        report_title = "Clinical Chemistry & Molecular Pathology"
        patient = {"name": data.get("patient_name", "Anonymous Patient"), "age": data.get("age", 45), "gender": data.get("gender", "Female"), "id": f"P-{int(time.time())%1000000}"}
        lab_name = "Automated AI Diagnostic Evaluation"
        image_url = uploaded_url if uploaded_url else "/static/samples/sample_diabetes_lipid.png"
        symptoms = user_symptoms or "Patient-uploaded diagnostic record."

        biomarkers = [
            {"key": "fbs", "name": "Fasting Plasma Glucose (FBS)", "value": 154.0, "unit": "mg/dL", "ref": "70.0 - 99.0", "status": "HIGH"},
            {"key": "hba1c", "name": "HbA1c (Glycated Hemoglobin)", "value": 7.9, "unit": "%", "ref": "4.0 - 5.6", "status": "HIGH"},
            {"key": "cholesterol", "name": "Total Cholesterol", "value": 232.0, "unit": "mg/dL", "ref": "125.0 - 200.0", "status": "HIGH"},
            {"key": "triglycerides", "name": "Serum Triglycerides", "value": 240.0, "unit": "mg/dL", "ref": "< 150.0", "status": "HIGH"},
            {"key": "ldl", "name": "LDL Cholesterol (Bad)", "value": 148.0, "unit": "mg/dL", "ref": "< 100.0", "status": "HIGH"},
            {"key": "hdl", "name": "HDL Cholesterol (Good)", "value": 42.0, "unit": "mg/dL", "ref": "> 40.0", "status": "NORMAL"},
            {"key": "hemoglobin", "name": "Hemoglobin (Hb)", "value": 13.5, "unit": "g/dL", "ref": "12.0 - 16.0", "status": "NORMAL"},
            {"key": "creatinine", "name": "Serum Creatinine", "value": 0.98, "unit": "mg/dL", "ref": "0.70 - 1.30", "status": "NORMAL"}
        ]

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
    file.save(filepath)

    return jsonify({
        "status": "success",
        "filename": filename,
        "url": f"/uploads/{filename}"
    })

# DOWNLOAD FULL ANTIGRAVITY FOOD & DIET (FOD) PLAN
@app.route('/api/download-diet-pdf', methods=['POST'])
def download_diet_pdf():
    data = request.get_json() or {}
    sample_id = data.get('sample_id', 'sample_diabetes_lipid')
    report = next((s for s in SAMPLE_REPORTS if s['id'] == sample_id), SAMPLE_REPORTS[0])
    biomarkers = report['biomarkers']
    diet_plan = generate_antigravity_diet_plan(biomarkers)

    w, h = 1800, 1400
    img = Image.new('RGB', (w, h), (15, 23, 42))
    draw = ImageDraw.Draw(img)

    # Header Banner
    draw.rectangle([40, 40, w - 40, 150], fill=(13, 148, 136))
    draw.text((70, 60), "ANTIGRAVITY AI CLINICAL NUTRITION: PERSONALIZED FOOD & DIET PROTOCOL", fill=(255, 255, 255))
    draw.text((70, 95), f"Patient: {report['patient']['name']} ({report['patient']['age']}Y/{report['patient']['gender']}) | Target: {diet_plan['calories']} | Hydration: {diet_plan['hydration']}", fill=(204, 251, 241))
    draw.text((w - 480, 75), "POWERED BY ANTIGRAVITY AI", fill=(251, 191, 36))

    # Diet Protocol Title & Macro Goals
    draw.rectangle([40, 170, w - 40, 240], fill=(30, 41, 59))
    draw.text((60, 185), f"CLINICAL PROTOCOL: {diet_plan['title'].upper()}", fill=(244, 63, 94))
    draw.text((60, 210), f"MACRONUTRIENT RATIO: {diet_plan['macros']}", fill=(226, 232, 240))

    # Schedule Table (Left / Center)
    sched_w = 1100
    draw.rectangle([40, 260, 40 + sched_w, h - 50], outline=(51, 65, 85), fill=(24, 33, 47), width=2)
    draw.text((60, 280), "24-HOUR PRECISION MEAL SCHEDULE & TIMING", fill=(45, 212, 191))

    row_y = 330
    for meal in diet_plan["schedule"]:
        draw.rectangle([60, row_y - 8, 40 + sched_w - 20, row_y + 85], fill=(30, 41, 59), outline=(51, 65, 85), width=1)
        draw.text((80, row_y), f"[{meal['time']}] {meal['meal'].upper()}", fill=(251, 191, 36))
        
        items_txt = meal['items']
        if len(items_txt) > 85:
            part1 = items_txt[:85]
            part2 = items_txt[85:]
            draw.text((80, row_y + 30), f"- {part1}", fill=(241, 245, 249))
            draw.text((80, row_y + 55), f"  {part2}", fill=(241, 245, 249))
        else:
            draw.text((80, row_y + 30), f"- {items_txt}", fill=(241, 245, 249))
        row_y += 115

    # Right Column: Superfoods & Red-Flag Prohibitions
    side_x = 40 + sched_w + 30
    side_w = w - side_x - 40
    draw.rectangle([side_x, 260, side_x + side_w, h - 50], outline=(51, 65, 85), fill=(24, 33, 47), width=2)

    draw.text((side_x + 25, 280), "THERAPEUTIC SUPERFOODS TO EAT:", fill=(34, 197, 94))
    sf_y = 320
    for sf in diet_plan["superfoods"]:
        draw.text((side_x + 35, sf_y), f"+ {sf}", fill=(209, 250, 229))
        sf_y += 40

    draw.line([(side_x + 20, sf_y + 20), (side_x + side_w - 20, sf_y + 20)], fill=(51, 65, 85), width=1)
    draw.text((side_x + 25, sf_y + 40), "STRICTLY PROHIBITED (RED FLAGS):", fill=(239, 68, 68))
    av_y = sf_y + 80
    for av in diet_plan["avoid_foods"]:
        draw.text((side_x + 35, av_y), f"- {av}", fill=(254, 202, 202))
        av_y += 45

    draw.rectangle([side_x + 20, h - 170, side_x + side_w - 20, h - 70], fill=(30, 41, 59), outline=(13, 148, 136), width=1)
    draw.text((side_x + 35, h - 155), "AI VERIFIED NUTRITION PROTOCOL", fill=(45, 212, 191))
    draw.text((side_x + 35, h - 130), "Calibrated for Patient Metabolic Profile", fill=(203, 213, 225))
    draw.text((side_x + 35, h - 105), "Engine: Antigravity Neural Bio-Nutrition", fill=(251, 191, 36))

    out_io = io.BytesIO()
    img.save(out_io, 'JPEG', quality=95)
    out_io.seek(0)

    return send_file(
        out_io,
        mimetype='image/jpeg',
        as_attachment=True,
        download_name=f"Antigravity_Food_Diet_Plan_{report['patient']['id']}.jpg"
    )

@app.route('/api/export-patient-summary', methods=['POST'])
def export_patient_summary():
    data = request.get_json() or {}
    sample_id = data.get('sample_id', 'sample_diabetes_lipid')
    report = next((s for s in SAMPLE_REPORTS if s['id'] == sample_id), SAMPLE_REPORTS[0])
    biomarkers = report['biomarkers']
    triage = evaluate_triage(biomarkers)

    w, h = 1800, 1200
    img = Image.new('RGB', (w, h), (15, 23, 42))
    draw = ImageDraw.Draw(img)

    draw.rectangle([40, 40, w - 40, 130], fill=(30, 41, 59))
    draw.text((70, 60), "MEDITRIAGE AI: PATIENT CLINICAL REPORT & TRIAGE ACTION PLAN", fill=(244, 63, 94))
    draw.text((70, 95), f"Patient: {report['patient']['name']} ({report['patient']['age']}Y/{report['patient']['gender']}) | Date: {report['date']}", fill=(226, 232, 240))
    draw.text((w - 440, 75), f"TRIAGE: {triage['urgency_label']}", fill=(251, 191, 36) if triage['urgency_color'] == 'amber' else ((239, 68, 68) if triage['urgency_color'] == 'red' else (34, 197, 94)))

    left_w = 700
    draw.rectangle([50, 150, 50 + left_w, h - 50], outline=(51, 65, 85), fill=(24, 33, 47), width=2)
    sample_path = os.path.join(SAMPLES_FOLDER, report['filename'])
    if os.path.exists(sample_path):
        with Image.open(sample_path) as s_img:
            resized_sample = s_img.resize((left_w - 40, h - 260))
            img.paste(resized_sample, (70, 210))
    draw.text((70, 170), "DIGITIZED CLINICAL LAB REPORT SCAN", fill=(56, 189, 248))

    right_x = 50 + left_w + 30
    right_w = w - right_x - 50
    draw.rectangle([right_x, 150, right_x + right_w, h - 50], outline=(51, 65, 85), fill=(24, 33, 47), width=2)
    draw.text((right_x + 30, 175), "AI BIOMARKER ANOMALY MATRIX & CLINICAL RECOMMENDATIONS", fill=(244, 63, 94))

    draw.rectangle([right_x + 30, 215, right_x + right_w - 30, 265], fill=(30, 41, 59))
    draw.text((right_x + 45, 230), f"Cardiometabolic Risk Index: {triage['risk_score']} / 100", fill=(255, 255, 255))
    draw.text((right_x + 450, 230), f"Urgency Timeframe: {triage['timeframe']}", fill=(251, 191, 36))

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
    for q in triage["doctor_questions"][:3]:
        draw.text((right_x + 40, q_y), f"> {q}", fill=(226, 232, 240))
        q_y += 35

    draw.text((right_x + 30, q_y + 20), "NUTRITION & LIFESTYLE GUIDANCE:", fill=(34, 197, 94))
    d_y = q_y + 55
    for item in triage["diet_plan"]["superfoods"][:3]:
        draw.text((right_x + 40, d_y), f"+ {item}", fill=(209, 250, 229))
        d_y += 35

    out_io = io.BytesIO()
    img.save(out_io, 'JPEG', quality=95)
    out_io.seek(0)

    return send_file(
        out_io,
        mimetype='image/jpeg',
        as_attachment=True,
        download_name=f"MediTriage_Clinical_Report_{report['patient']['id']}.jpg"
    )

if __name__ == '__main__':
    print("Starting MediTriage AI Server on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)
