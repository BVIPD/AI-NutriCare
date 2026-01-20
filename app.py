import streamlit as st
import pandas as pd
import pdfplumber
import re
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="AI-NutritionalCare",
    page_icon="🥗",
    layout="centered"
)

# --------------------------------------------------
# SOFT GRADIENT BACKGROUND (OPTION 2 - SUBTLE)
# --------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(to bottom, #f6fff8, #ffffff);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# HEADER IMAGE (OPTION 1 - SAFE & CLASSY)
# --------------------------------------------------
st.image(
    "https://images.unsplash.com/photo-1498837167922-ddd27525d352",
    use_column_width=True
)

st.title("🥗 AI-NutritionalCare")
st.caption("AI-driven Personalized Diet Recommendation System")
st.divider()

# --------------------------------------------------
# UTILITIES
# --------------------------------------------------
def extract_text(file):
    ext = file.name.split(".")[-1].lower()
    text = ""

    if ext == "pdf":
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"

    elif ext == "csv":
        df = pd.read_csv(file)
        text = " ".join(df.astype(str).iloc[0].values)

    elif ext == "txt":
        text = file.read().decode("utf-8")

    return text.strip()


def extract_patient_name(text):
    patterns = [
        r"patient\s*name\s*[:\-]\s*([A-Za-z ]+)",
        r"patient\s*[:\-]\s*([A-Za-z ]+)"
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return "Unknown Patient"


def extract_conditions(text):
    conditions = []
    t = text.lower()
    if "diabetes" in t:
        conditions.append("Diabetes")
    if "cholesterol" in t:
        conditions.append("High Cholesterol")
    if "hypertension" in t or "blood pressure" in t:
        conditions.append("Hypertension")
    return conditions if conditions else ["General Health"]

# --------------------------------------------------
# MEALS (NO INGREDIENTS / NO COOKING STEPS)
# --------------------------------------------------
VEG_MEALS = [
    "Vegetable Khichdi","Chapati & Veg Sabzi","Vegetable Upma","Oats Porridge",
    "Curd Rice","Vegetable Dalia","Paneer Bhurji","Lemon Rice",
    "Idli & Sambar","Vegetable Poha","Rajma Rice","Veg Pulao",
    "Sprouts Salad","Tomato Soup","Veg Sandwich","Masala Oats",
    "Curd Bowl","Veg Fried Rice","Paneer Salad","Veg Soup",
    "Ragi Porridge","Dal & Chapati","Veg Cutlet","Fruit Bowl",
    "Vegetable Khichdi","Chapati & Veg Sabzi","Vegetable Upma","Oats Porridge"
]

NONVEG_MEALS = [
    "Egg Omelette","Grilled Chicken","Fish Curry","Boiled Eggs",
    "Chicken Soup","Egg Fried Rice","Grilled Fish","Chicken Sandwich",
    "Egg Bhurji","Chicken Pulao","Fish Fry","Chicken Curry",
    "Egg Curry","Chicken Salad","Fish Soup","Egg Toast",
    "Chicken Wrap","Fish Rice Bowl","Egg Salad","Chicken Stir Fry",
    "Fish Lemon Curry","Egg Rice","Chicken Stew","Protein Bowl",
    "Egg Omelette","Grilled Chicken","Fish Curry","Boiled Eggs"
]

def generate_month_plan(pref):
    meals = VEG_MEALS if pref == "Vegetarian" else NONVEG_MEALS
    return meals[:28]

# --------------------------------------------------
# PDF GENERATOR
# --------------------------------------------------
def generate_pdf(patient, conditions, plan):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "AI-NutritionalCare Diet Report")
    y -= 30

    c.setFont("Helvetica", 11)
    c.drawString(40, y, f"Patient: {patient}")
    y -= 20
    c.drawString(40, y, f"Medical Conditions: {', '.join(conditions)}")
    y -= 30

    for i, food in enumerate(plan, 1):
        if y < 80:
            c.showPage()
            y = height - 40

        c.setFont("Helvetica", 11)
        c.drawString(40, y, f"Day {i}: {food}")
        y -= 18

    c.save()
    buffer.seek(0)
    return buffer

# --------------------------------------------------
# INPUT UI
# --------------------------------------------------
uploaded = st.file_uploader("📄 Upload Medical Report (PDF / CSV / TXT)", type=["pdf","csv","txt"])
preference = st.radio("🥦 Food Preference", ["Vegetarian", "Non-Vegetarian"])
run = st.button("✨ Generate Diet Recommendation")

# --------------------------------------------------
# OUTPUT
# --------------------------------------------------
if run:
    if not uploaded:
        st.warning("Please upload a medical report.")
        st.stop()

    raw_text = extract_text(uploaded)
    patient = extract_patient_name(raw_text)
    conditions = extract_conditions(raw_text)
    month_plan = generate_month_plan(preference)

    st.subheader("📄 Output")
    st.markdown(f"""
**Patient:** {patient}  
**Medical Condition:** {', '.join(conditions)}  
**Listing 1:** AI-Generated Personalized Diet Plan
""")

    st.subheader("📅 1-Month Diet Plan (Day-wise)")
    tabs = st.tabs(["Week 1","Week 2","Week 3","Week 4"])

    idx = 0
    for tab in tabs:
        with tab:
            for _ in range(7):
                st.success(f"🍽️ Day {idx+1}: {month_plan[idx]}")
                idx += 1

    # Downloads
    st.download_button(
        "⬇️ Download JSON",
        data=pd.Series({
            "patient": patient,
            "conditions": conditions,
            "diet_plan": month_plan
        }).to_json(),
        file_name="diet_plan.json",
        mime="application/json"
    )

    pdf = generate_pdf(patient, conditions, month_plan)
    st.download_button(
        "⬇️ Download PDF",
        data=pdf,
        file_name=f"{patient.replace(' ','_')}_DietPlan.pdf",
        mime="application/pdf"
    )

st.divider()
st.caption("© AI-NutritionalCare | Internship Final Submission")
