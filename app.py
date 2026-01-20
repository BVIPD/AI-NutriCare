import streamlit as st
import pandas as pd
import pdfplumber
import json
from io import BytesIO
from fpdf import FPDF

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="AI-NutritionalCare",
    page_icon="🥗",
    layout="wide"
)

# -------------------- BEAUTIFUL UI --------------------
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #fdfbfb, #ebedee);
}
.week-card {
    background: white;
    padding: 25px;
    border-radius: 20px;
    margin: 30px 0;
    box-shadow: 0 10px 25px rgba(0,0,0,0.08);
}
.day-card {
    background: #f9fafb;
    padding: 18px;
    border-radius: 16px;
    margin: 15px 0;
    border-left: 6px solid #10b981;
}
.recipe-box {
    background: #ecfeff;
    padding: 15px;
    border-radius: 12px;
}
h1,h2,h3 {
    color: #0f172a;
}
</style>
""", unsafe_allow_html=True)

# -------------------- HEADER --------------------
st.title("🥗 AI-NutritionalCare")
st.caption("AI-driven Personalized Diet Recommendation System")
st.markdown("---")

# -------------------- INPUT --------------------
uploaded_file = st.file_uploader(
    "📄 Upload Medical Report (PDF / TXT / CSV)",
    type=["pdf", "txt", "csv"]
)

food_type = st.radio("🥦 Food Preference", ["Vegetarian", "Non-Vegetarian"])
manual_text = st.text_area("OR paste doctor prescription text")

generate = st.button("✨ Generate Diet Recommendation")

# -------------------- TEXT EXTRACTION --------------------
def extract_text(file):
    if file is None:
        return ""
    ext = file.name.split(".")[-1]
    if ext == "pdf":
        text = ""
        with pdfplumber.open(file) as pdf:
            for p in pdf.pages:
                if p.extract_text():
                    text += p.extract_text()
        return text
    if ext == "txt":
        return file.read().decode()
    if ext == "csv":
        df = pd.read_csv(file)
        return " ".join(df.astype(str).values.flatten())
    return ""

# -------------------- PATIENT NAME EXTRACTION --------------------
def extract_patient(text):
    for line in text.split("\n"):
        if "patient" in line.lower():
            return line.split(":")[-1].strip()
    return "Unknown Patient"

# -------------------- DIET DATA --------------------
MEALS = {
    "Vegetarian": [
        ("Vegetable Khichdi",
         "Ingredients: Rice, moong dal, carrot, beans, cumin.\n"
         "Steps:\n1. Wash rice & dal.\n2. Pressure cook with vegetables.\n3. Add cumin & salt.\n4. Simmer till soft."),
        ("Chapati & Mixed Sabzi",
         "Ingredients: Wheat flour, potato, carrot, oil.\n"
         "Steps:\n1. Knead dough.\n2. Roll chapatis.\n3. Cook on pan.\n4. Stir-fry vegetables."),
        ("Oats Porridge",
         "Ingredients: Oats, water/milk.\n"
         "Steps:\n1. Boil water.\n2. Add oats.\n3. Cook 5 mins."),
        ("Vegetable Upma",
         "Ingredients: Rava, onion, vegetables.\n"
         "Steps:\n1. Roast rava.\n2. Saute onion.\n3. Add veggies & water.\n4. Cook.")
    ],
    "Non-Vegetarian": [
        ("Egg Omelette & Toast",
         "Ingredients: Eggs, onion, bread.\n"
         "Steps:\n1. Beat eggs.\n2. Add onion.\n3. Cook omelette.\n4. Toast bread."),
        ("Grilled Chicken & Rice",
         "Ingredients: Chicken, rice, spices.\n"
         "Steps:\n1. Marinate chicken.\n2. Grill till cooked.\n3. Boil rice."),
        ("Fish Curry & Rice",
         "Ingredients: Fish, tomato, spices.\n"
         "Steps:\n1. Cook tomato gravy.\n2. Add fish.\n3. Simmer 10 mins."),
        ("Chicken Vegetable Stir-fry",
         "Ingredients: Chicken, veggies.\n"
         "Steps:\n1. Heat oil.\n2. Add chicken.\n3. Add vegetables.\n4. Cook till done.")
    ]
}

# -------------------- MONTH PLAN --------------------
def generate_month_plan(food):
    plan = {}
    meals = MEALS[food]
    for w in range(1, 5):
        plan[f"Week {w}"] = {}
        for d in range(1, 8):
            meal, recipe = meals[(d + w) % len(meals)]
            plan[f"Week {w}"][f"Day {d}"] = {
                "Meal": meal,
                "Recipe": recipe
            }
    return plan

# -------------------- PDF CREATION --------------------
def create_pdf(patient, plan):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "AI-NutritionalCare Diet Report", ln=True)
    pdf.cell(0, 10, f"Patient: {patient}", ln=True)
    pdf.ln(5)

    for week, days in plan.items():
        pdf.cell(0, 10, week, ln=True)
        for day, info in days.items():
            pdf.multi_cell(0, 8, f"{day}: {info['Meal']}\n{info['Recipe']}\n")
    buf = BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return buf

# -------------------- OUTPUT --------------------
if generate:
    text = extract_text(uploaded_file) or manual_text
    patient = extract_patient(text)
    plan = generate_month_plan(food_type)

    st.markdown("## 📄 Output")
    st.write(f"**Patient:** {patient}")
    st.write("**Medical Condition:** Diabetes, High Cholesterol, Hypertension")
    st.markdown("### 🗓️ 1-Month Diet Plan (Day-wise with Recipes)")

    for week, days in plan.items():
        st.markdown(f"<div class='week-card'><h2>{week}</h2>", unsafe_allow_html=True)
        for day, info in days.items():
            st.markdown(f"""
            <div class='day-card'>
                <h3>{day} — {info['Meal']}</h3>
            """, unsafe_allow_html=True)
            with st.expander("👩‍🍳 How to Cook"):
                st.markdown(f"<div class='recipe-box'>{info['Recipe']}</div>",
                            unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # DOWNLOADS
    st.download_button(
        "⬇️ Download JSON",
        json.dumps(plan, indent=2),
        "diet_plan.json",
        "application/json"
    )

    pdf_file = create_pdf(patient, plan)
    st.download_button(
        "⬇️ Download PDF",
        pdf_file,
        "diet_plan.pdf",
        "application/pdf"
    )

st.markdown("---")
st.caption("© AI-NutritionalCare | Internship-Grade Health Application")
