import os
from PIL import Image, ImageDraw, ImageFont

def draw_lab_report(path, header_title, patient_info, test_title, test_rows):
    w, h = 1200, 1600
    bg_color = (255, 255, 255)
    border_color = (203, 213, 225)
    header_bg = (241, 245, 249)
    text_dark = (15, 23, 42)
    text_muted = (100, 116, 139)
    flag_high = (220, 38, 38)
    flag_low = (37, 99, 235)
    flag_normal = (22, 163, 74)

    img = Image.new("RGB", (w, h), bg_color)
    draw = ImageDraw.Draw(img)

    # Outer border
    draw.rectangle([30, 30, w - 30, h - 30], outline=border_color, width=2)
    draw.rectangle([34, 34, w - 34, h - 34], outline=border_color, width=1)

    # 1. Hospital Header
    draw.rectangle([36, 36, w - 36, 180], fill=(248, 250, 252))
    # Red Cross Icon
    draw.rectangle([60, 65, 110, 150], fill=(225, 29, 72))
    draw.rectangle([40, 85, 130, 130], fill=(225, 29, 72))

    draw.text((150, 60), header_title.upper(), fill=(14, 116, 144))
    draw.text((150, 95), "NABH & NABL ACCREDITED CLINICAL PATHOLOGY LABORATORY", fill=text_muted)
    draw.text((150, 120), "Reg No: MED-LAB-2026-9842 | Automated Molecular Diagnostics", fill=text_muted)

    draw.line([(36, 180), (w - 36, 180)], fill=(14, 116, 144), width=3)

    # 2. Patient Demographics Box
    draw.rectangle([50, 200, w - 50, 320], outline=border_color, fill=(248, 250, 252), width=1)
    
    col1_x, col2_x, col3_x = 70, 480, 850
    y_start = 220
    draw.text((col1_x, y_start), f"Patient Name:  {patient_info['name']}", fill=text_dark)
    draw.text((col1_x, y_start + 30), f"Age / Gender:  {patient_info['age_gender']}", fill=text_dark)
    draw.text((col1_x, y_start + 60), f"Patient ID:    {patient_info['pid']}", fill=text_muted)

    draw.text((col2_x, y_start), f"Referred By:   {patient_info['ref_by']}", fill=text_dark)
    draw.text((col2_x, y_start + 30), f"Sample Type:   {patient_info['sample']}", fill=text_dark)
    draw.text((col2_x, y_start + 60), f"Collection:    {patient_info['collection_date']}", fill=text_muted)

    draw.text((col3_x, y_start), f"Report ID:     {patient_info['barcode']}", fill=text_dark)
    draw.text((col3_x, y_start + 30), f"Reporting:     {patient_info['report_date']}", fill=text_dark)
    draw.text((col3_x, y_start + 60), f"Status:        FINAL VERIFIED", fill=flag_normal)

    # 3. Test Title Banner
    draw.rectangle([50, 350, w - 50, 400], fill=(224, 242, 254))
    draw.text((70, 365), f"DEPARTMENT OF BIOCHEMISTRY: {test_title.upper()}", fill=(3, 105, 161))

    # 4. Table Header
    draw.rectangle([50, 420, w - 50, 465], fill=(241, 245, 249), outline=border_color, width=1)
    draw.text((70, 432), "INVESTIGATION / PARAMETER", fill=text_dark)
    draw.text((500, 432), "OBSERVED VALUE", fill=text_dark)
    draw.text((730, 432), "REFERENCE RANGE", fill=text_dark)
    draw.text((950, 432), "UNIT", fill=text_dark)
    draw.text((1050, 432), "STATUS", fill=text_dark)

    # 5. Table Rows
    row_y = 480
    for row in test_rows:
        draw.line([(50, row_y - 8), (w - 50, row_y - 8)], fill=(241, 245, 249), width=1)
        
        # Determine status color
        status_color = text_dark
        if row["status"] == "HIGH":
            status_color = flag_high
        elif row["status"] == "CRITICAL HIGH":
            status_color = flag_high
        elif row["status"] == "LOW":
            status_color = flag_low
        elif row["status"] == "NORMAL":
            status_color = flag_normal

        draw.text((70, row_y), row["name"], fill=text_dark)
        draw.text((500, row_y), str(row["value"]), fill=status_color)
        draw.text((730, row_y), row["ref"], fill=text_muted)
        draw.text((950, row_y), row["unit"], fill=text_muted)
        
        # Status pill
        draw.rectangle([1040, row_y - 2, 1140, row_y + 22], fill=(254, 226, 226) if "HIGH" in row["status"] else ((219, 234, 254) if "LOW" in row["status"] else (220, 252, 231)))
        draw.text((1050, row_y + 2), row["status"][:8], fill=status_color)

        row_y += 45

    # 6. Clinical Remarks & QR / Signatures
    foot_y = h - 260
    draw.rectangle([50, foot_y, w - 50, h - 60], outline=border_color, fill=(248, 250, 252), width=1)
    draw.text((70, foot_y + 15), "CLINICAL REMARKS & METHODOLOGY:", fill=text_dark)
    draw.text((70, foot_y + 40), "• Test performed using automated chemiluminescence immunoassay (CLIA) and spectrophotometry.", fill=text_muted)
    draw.text((70, foot_y + 65), "• Values outside reference limits should be correlated with clinical symptoms by treating physician.", fill=text_muted)
    draw.text((70, foot_y + 90), "• Biological reference intervals are standardized for adult fasting profile.", fill=text_muted)

    # Doctor Signature block
    draw.line([(880, foot_y + 130), (1120, foot_y + 130)], fill=text_muted, width=1)
    draw.text((880, foot_y + 140), "Dr. S. K. Kulkarni, MD (Path)", fill=text_dark)
    draw.text((880, foot_y + 160), "Consultant Clinical Pathologist", fill=text_muted)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, quality=95)
    print(f"Generated sample report at: {path}")

if __name__ == "__main__":
    base = r"C:\Users\Admin\.gemini\antigravity\scratch\meditriage-ai\static\samples"
    
    # 1. Diabetic & Lipid Panel
    p1 = {
        "name": "Rahul Sharma",
        "age_gender": "48 Y / Male",
        "pid": "P-984210",
        "ref_by": "Dr. A. Verma (MBBS, MD)",
        "sample": "Venous Whole Blood & Serum",
        "collection_date": "28-Oct-2026 08:30 AM",
        "report_date": "28-Oct-2026 11:45 AM",
        "barcode": "LAB-261028-091"
    }
    rows1 = [
        {"name": "Fasting Plasma Glucose (FBS)", "value": 168.0, "ref": "70.0 - 99.0", "unit": "mg/dL", "status": "HIGH"},
        {"name": "Post-Prandial Glucose (PPBS)", "value": 245.0, "ref": "< 140.0", "unit": "mg/dL", "status": "CRITICAL HIGH"},
        {"name": "HbA1c (Glycated Hemoglobin)", "value": 8.4, "ref": "4.0 - 5.6", "unit": "%", "status": "HIGH"},
        {"name": "Estimated Average Glucose (eAG)", "value": 194.0, "ref": "70 - 114", "unit": "mg/dL", "status": "HIGH"},
        {"name": "Total Cholesterol", "value": 248.0, "ref": "125.0 - 200.0", "unit": "mg/dL", "status": "HIGH"},
        {"name": "Serum Triglycerides", "value": 280.0, "ref": "< 150.0", "unit": "mg/dL", "status": "HIGH"},
        {"name": "LDL Cholesterol (Calculated)", "value": 162.0, "ref": "< 100.0", "unit": "mg/dL", "status": "HIGH"},
        {"name": "HDL Cholesterol (Good)", "value": 38.0, "ref": "> 40.0", "unit": "mg/dL", "status": "LOW"},
        {"name": "Serum Creatinine", "value": 1.05, "ref": "0.70 - 1.30", "unit": "mg/dL", "status": "NORMAL"},
        {"name": "Blood Urea Nitrogen (BUN)", "value": 16.0, "ref": "7.0 - 20.0", "unit": "mg/dL", "status": "NORMAL"}
    ]
    draw_lab_report(os.path.join(base, "sample_diabetes_lipid.png"), "MetroHealth Diagnostics & Labs", p1, "Comprehensive Diabetic & Lipid Profile", rows1)

    # 2. CBC Anemia & Infection Panel
    p2 = {
        "name": "Pooja Patel",
        "age_gender": "26 Y / Female",
        "pid": "P-984211",
        "ref_by": "Dr. R. Mehta (MBBS)",
        "sample": "EDTA Whole Blood",
        "collection_date": "28-Oct-2026 09:15 AM",
        "report_date": "28-Oct-2026 12:10 PM",
        "barcode": "LAB-261028-092"
    }
    rows2 = [
        {"name": "Hemoglobin (Hb)", "value": 9.2, "ref": "12.0 - 15.5", "unit": "g/dL", "status": "LOW"},
        {"name": "Total Leucocyte Count (WBC)", "value": 14800, "ref": "4000 - 11000", "unit": "/mcL", "status": "HIGH"},
        {"name": "Neutrophils", "value": 78, "ref": "40 - 70", "unit": "%", "status": "HIGH"},
        {"name": "Lymphocytes", "value": 18, "ref": "20 - 40", "unit": "%", "status": "LOW"},
        {"name": "RBC Count", "value": 3.42, "ref": "3.80 - 5.20", "unit": "mil/mcL", "status": "LOW"},
        {"name": "Platelet Count", "value": 215000, "ref": "150000 - 450000", "unit": "/mcL", "status": "NORMAL"},
        {"name": "Packed Cell Volume (PCV)", "value": 29.5, "ref": "36.0 - 46.0", "unit": "%", "status": "LOW"},
        {"name": "ESR (Westergren)", "value": 38, "ref": "0 - 20", "unit": "mm/1st hr", "status": "HIGH"}
    ]
    draw_lab_report(os.path.join(base, "sample_cbc_infection.png"), "Apex Care Pathology Laboratory", p2, "Complete Blood Count (CBC) with Differential", rows2)

    # 3. Healthy Normal Baseline
    p3 = {
        "name": "Amit Deshmukh",
        "age_gender": "32 Y / Male",
        "pid": "P-984212",
        "ref_by": "Self Checkup",
        "sample": "Serum & Whole Blood",
        "collection_date": "28-Oct-2026 07:45 AM",
        "report_date": "28-Oct-2026 10:30 AM",
        "barcode": "LAB-261028-093"
    }
    rows3 = [
        {"name": "Fasting Plasma Glucose (FBS)", "value": 88.0, "ref": "70.0 - 99.0", "unit": "mg/dL", "status": "NORMAL"},
        {"name": "HbA1c", "value": 5.2, "ref": "4.0 - 5.6", "unit": "%", "status": "NORMAL"},
        {"name": "Total Cholesterol", "value": 165.0, "ref": "125.0 - 200.0", "unit": "mg/dL", "status": "NORMAL"},
        {"name": "Serum Triglycerides", "value": 110.0, "ref": "< 150.0", "unit": "mg/dL", "status": "NORMAL"},
        {"name": "LDL Cholesterol", "value": 92.0, "ref": "< 100.0", "unit": "mg/dL", "status": "NORMAL"},
        {"name": "HDL Cholesterol", "value": 51.0, "ref": "> 40.0", "unit": "mg/dL", "status": "NORMAL"},
        {"name": "Hemoglobin", "value": 14.8, "ref": "13.0 - 17.0", "unit": "g/dL", "status": "NORMAL"},
        {"name": "Serum Creatinine", "value": 0.95, "ref": "0.70 - 1.30", "unit": "mg/dL", "status": "NORMAL"}
    ]
    draw_lab_report(os.path.join(base, "sample_normal_baseline.png"), "Wellness Diagnostic Imaging", p3, "Annual Wellness Health Screen", rows3)
