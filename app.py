import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
import re
import json
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="AI-NutritionalCare",
    page_icon="🥗",
    layout="centered"
)

# -------------------- HEADER --------------------
st.markdown("""
<h1 style='text-align:center;'>🥗 AI-NutritionalCare</h1>
<p style='text-align:center;color:gray;'>AI-driven Personalized Diet Recommendation System</p>
<hr>
""", unsafe_allow_html=True)

# -------------------- HELPERS --------------------
def extract_patient_name(text):
    match = re.search(r"(patient name|patient)[:\- ]+([A-Za-z ]+)", text, re.I)
    return match.group(2).strip() if match else "Unknown Patient"

def extract_text(uploaded_file):
    ext = uploaded_file.name.split(".")[-1].lower()
    text = ""

    if ext == "pdf":
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                if page.extract_text():
                    text += page.extract_text() + "\n"

    elif ext in ["png", "jpg", "jpeg"]:
        try:
            img = Image.open(uploaded_file)
            text = pytesseract.image_to_string(img)
        except:
            text = ""

    elif ext == "txt":
        text = uploaded_file.read().decode("utf-8")

    elif ext == "csv":
        df = pd.read_csv(uploaded_file)
        text = " ".join(df.astype(str).iloc[0].values)

    return text.strip()

# -------------------- DIET LOGIC --------------------
def infer_conditions(text):
    text = text.lower()
    conditions = []
    if "diabetes" in text:
        conditions.append("Diabetes")
    if "cholesterol" in text:
        conditions.append("High Cholesterol")
    if "hypertension" in text or "blood pressure" in text:
        conditions.append("Hypertension")
    return conditions or ["General Health"]

# -------------------- MONTHLY DIET --------------------
def monthly_diet(veg=True):
    if veg:
        return {
            "Week 1": [
                ("Vegetable Upma",
                 "Ingredients: Rava, vegetables, oil.\n"
                 "Steps: Dry roast rava. Heat oil, saute veggies, add water, add rava, cook till soft."),
                ("Dal Rice",
                 "Ingredients: Rice, moong dal.\n"
                 "Steps: Pressure cook rice and dal with turmeric and salt.")
            ],
            "Week 2": [
                ("Oats Porridge",
                 "Ingredients: Oats, milk, fruits.\n"
                 "Steps: Cook oats in milk, top with fruits."),
                ("Vegetable Khichdi",
                 "Ingredients: Rice, dal, vegetables.\n"
                 "Steps: Pressure cook all ingredients together.")
            ],
            "Week 3": [
                ("Idli & Sambar",
                 "Ingredients: Idli batter, dal, vegetables.\n"
                 "Steps: Steam idlis, cook sambar separately."),
                ("Curd Rice",
                 "Ingredients: Rice, curd.\n"
                 "Steps: Mix cooked rice with curd and salt.")
            ],
            "Week 4": [
                ("Poha",
                 "Ingredients: Flattened rice, peanuts.\n"
                 "Steps: Soak poha, saute peanuts, mix and cook."),
                ("Chapati & Vegetable Sabzi",
                 "Chapati: Knead wheat flour, roll, cook on pan.\n"
                 "Sabzi: Cook vegetables with oil and spices.")
            ]
        }
    else:
        return {
            "Week 1": [
                ("Egg Omelette & Toast",
                 "Ingredients: Eggs, onion.\n"
                 "Steps: Beat eggs, cook on pan."),
                ("Grilled Chicken & Rice",
                 "Ingredients: Chicken, rice.\n"
                 "Steps: Grill chicken, serve with rice.")
            ],
            "Week 2": [
                ("Boiled Eggs & Fruits",
                 "Steps: Boil eggs for 10 minutes."),
                ("Fish Curry & Rice",
                 "Steps: Cook fish with spices and tomato.")
            ],
            "Week 3": [
                ("Chicken Sandwich",
                 "Steps: Grill chicken, assemble sandwich."),
                ("Egg Fried Rice",
                 "Steps: Stir fry rice with egg.")
            ],
            "Week 4": [
                ("Scrambled Eggs",
                 "Steps: Cook beaten eggs."),
                ("Chicken Soup",
                 "Steps: Boil chicken with vegetables.")
            ]
        }

# -------------------- PDF GENERATOR --------------------
def create_pdf(patient, conditions, plan):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 40

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, "AI-NutritionalCare Diet Report")
    y -= 40

    c.setFont("Helvetica", 11)
    c.drawString(40, y, f"Patient: {patient}")
    y -= 20
    c.drawString(40, y, f"Medical Conditions: {', '.join(conditions)}")
    y -= 30

    for week, meals in plan.items():
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, week)
        y -= 20
        c.setFont("Helvetica", 10)
        for meal, recipe in meals:
            c.drawString(50, y, f"{meal}: {recipe.splitlines()[0]}")
            y -= 15
        y -= 10

    c.save()
    buffer.seek(0)
    return buffer

# -------------------- UI INPUT --------------------
st.subheader("📄 Upload Medical Report")

patient_pref = st.radio("Food Preference", ["Vegetarian", "Non-Vegetarian"])

uploaded = st.file_uploader("Upload PDF / Image / TXT / CSV", type=["pdf","png","jpg","jpeg","txt","csv"])
manual_text = st.text_area("OR paste prescription text")

if st.button("🔍 Generate Diet Recommendation"):
    text = extract_text(uploaded) if uploaded else manual_text
    patient = extract_patient_name(text)
    conditions = infer_conditions(text)
    plan = monthly_diet(patient_pref == "Vegetarian")

    # -------------------- OUTPUT --------------------
    st.markdown("## 📋 Output")
    st.code(f"""
Patient: {patient}
Medical Condition: {', '.join(conditions)}
Listing 1: Sample Diet Plan from AI-NutritionalCare
""")

    st.markdown("## 📅 1-Month Diet Plan (With Recipes)")
    for week, meals in plan.items():
        with st.expander(week):
            for meal, recipe in meals:
                st.markdown(f"**{meal}**")
                st.text(recipe)

    # -------------------- DOWNLOADS --------------------
    st.download_button(
        "⬇️ Download JSON",
        json.dumps(plan, indent=2),
        file_name="diet_plan.json"
    )

    pdf = create_pdf(patient, conditions, plan)
    st.download_button(
        "⬇️ Download PDF",
        pdf,
        file_name=f"{patient}_DietPlan.pdf",
        mime="application/pdf"
    )

st.markdown("<hr><center>© AI-NutritionalCare | Final Internship Submission</center>", unsafe_allow_html=True)
