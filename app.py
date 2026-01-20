import streamlit as st
import pandas as pd
import pdfplumber
import re
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# --------------------------------------------------
# PAGE CONFIG (DO NOT CHANGE)
# --------------------------------------------------
st.set_page_config(
    page_title="AI-NutritionalCare",
    page_icon="🥗",
    layout="centered"
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
# DIET DATA (BEGINNER-LEVEL RECIPES)
# --------------------------------------------------
VEG_MEALS = [
    ("Vegetable Khichdi","Rice, dal, carrot, beans"),
    ("Chapati & Veg Sabzi","Wheat flour, mixed vegetables"),
    ("Vegetable Upma","Rava, onion, vegetables"),
    ("Oats Porridge","Oats, water"),
    ("Curd Rice","Rice, curd"),
    ("Vegetable Dalia","Broken wheat, vegetables"),
    ("Paneer Bhurji","Paneer, onion"),
    ("Lemon Rice","Rice, lemon"),
    ("Idli & Sambar","Idli batter, lentils"),
    ("Vegetable Poha","Poha, peanuts"),
    ("Rajma Rice","Rajma, rice"),
    ("Stuffed Paratha","Wheat flour, potato"),
    ("Veg Pulao","Rice, vegetables"),
    ("Sprouts Salad","Sprouts"),
    ("Tomato Soup","Tomato"),
    ("Veg Sandwich","Bread, vegetables"),
    ("Masala Oats","Oats, vegetables"),
    ("Curd Bowl","Curd, cucumber"),
    ("Veg Fried Rice","Rice, vegetables"),
    ("Paneer Salad","Paneer, vegetables"),
    ("Veg Soup","Mixed vegetables"),
    ("Ragi Porridge","Ragi flour"),
    ("Cabbage Fry","Cabbage"),
    ("Besan Omelette","Besan"),
    ("Dal & Chapati","Dal, wheat chapati"),
    ("Veg Cutlet","Mixed vegetables"),
    ("Bottle Gourd Khichdi","Rice, dal, bottle gourd"),
    ("Fruit Bowl","Seasonal fruits")
]
NONVEG_MEALS = [
    ("Egg Omelette","Eggs, onion"),
    ("Grilled Chicken","Chicken"),
    ("Fish Curry","Fish"),
    ("Boiled Eggs","Eggs"),
    ("Chicken Soup","Chicken"),
    ("Egg Fried Rice","Rice, egg"),
    ("Grilled Fish","Fish"),
    ("Chicken Sandwich","Bread, chicken"),
    ("Egg Bhurji","Eggs"),
    ("Chicken Pulao","Rice, chicken"),
    ("Fish Fry","Fish"),
    ("Chicken Curry","Chicken"),
    ("Egg Curry","Eggs"),
    ("Chicken Salad","Chicken"),
    ("Fish Soup","Fish"),
    ("Egg Toast","Eggs, bread"),
    ("Chicken Wrap","Chapati, chicken"),
    ("Grilled Chicken Veg","Chicken, vegetables"),
    ("Fish Rice Bowl","Fish, rice"),
    ("Egg Salad","Eggs"),
    ("Chicken Stir Fry","Chicken"),
    ("Fish Lemon Curry","Fish"),
    ("Egg Rice","Eggs, rice"),
    ("Chicken Stew","Chicken"),
    ("Fish Stew","Fish"),
    ("Egg Paratha","Eggs, wheat flour"),
    ("Chicken Cutlet","Chicken"),
    ("Protein Bowl","Chicken, eggs")
]


def generate_month_plan(pref):
    meals = VEG_MEALS if pref == "Vegetarian" else NONVEG_MEALS
    month = []
    for i in range(28):
        month.append(meals[i % len(meals)])
    return month


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

    day = 1
    for food, ing, steps in plan:
        if y < 100:
            c.showPage()
            y = height - 40

        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, y, f"Day {day}: {food}")
        y -= 15

        c.setFont("Helvetica", 10)
        c.drawString(50, y, f"Ingredients: {ing}")
        y -= 15
        c.drawString(50, y, f"Steps: {steps}")
        y -= 20

        day += 1

    c.save()
    buffer.seek(0)
    return buffer


# --------------------------------------------------
# INPUT UI
# --------------------------------------------------
uploaded = st.file_uploader("📄 Upload Medical Report (PDF / CSV / TXT)", type=["pdf", "csv", "txt"])
preference = st.radio("🥦 Food Preference", ["Vegetarian", "Non-Vegetarian"])
run = st.button("✨ Generate Diet Recommendation")

# --------------------------------------------------
# OUTPUT
# --------------------------------------------------
if run:
    if not uploaded:
        st.warning("Please upload a file.")
        st.stop()

    raw_text = extract_text(uploaded)
    patient = extract_patient_name(raw_text)
    conditions = extract_conditions(raw_text)
    month_plan = generate_month_plan(preference)

    # ---------- Sir-Style Output ----------
    st.subheader("📄 Output")
    st.markdown(f"""
**Patient:** {patient}  
**Medical Condition:** {', '.join(conditions)}  
**Listing 1:** Sample Diet Plan from AI-NutritionalCare
""")

    # ---------- Month Plan ----------
    st.subheader("📅 1-Month Diet Plan (Day-wise with Recipes)")
    tabs = st.tabs(["Week 1", "Week 2", "Week 3", "Week 4"])

    day_index = 0
    for w, tab in enumerate(tabs):
        with tab:
            for d in range(7):
                food, ing, steps = month_plan[day_index]
                with st.expander(f"🍽️ Day {day_index + 1}: {food}"):
                    st.markdown("**🧺 Ingredients**")
                    st.write(ing)
                    st.markdown("**👩‍🍳 How to Cook**")
                    for i, s in enumerate(steps.split("."), 1):
                        if s.strip():
                            st.write(f"{i}. {s.strip()}")
                day_index += 1

    # ---------- Downloads ----------
    diet_json = {
        "patient": patient,
        "conditions": conditions,
        "diet_plan": [
            {"day": i + 1, "meal": m[0], "ingredients": m[1], "steps": m[2]}
            for i, m in enumerate(month_plan)
        ]
    }

    st.download_button(
        "⬇️ Download JSON",
        data=pd.Series(diet_json).to_json(),
        file_name="diet_plan.json",
        mime="application/json"
    )

    pdf_file = generate_pdf(patient, conditions, month_plan)
    st.download_button(
        "⬇️ Download PDF",
        data=pdf_file,
        file_name=f"{patient.replace(' ', '_')}_DietPlan.pdf",
        mime="application/pdf"
    )
