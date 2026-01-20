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
    ("Vegetable Khichdi","Rice, dal, carrot, beans","Wash rice & dal. Pressure cook with vegetables & salt."),
    ("Chapati & Veg Sabzi","Wheat flour, vegetables","Knead dough. Roll chapati. Stir-fry vegetables."),
    ("Vegetable Upma","Rava, onion, vegetables","Roast rava. Cook with veggies & water."),
    ("Oats Porridge","Oats, water","Boil water. Add oats. Cook 5–7 mins."),
    ("Curd Rice","Rice, curd","Mix cooked rice with curd & salt."),
    ("Vegetable Dalia","Broken wheat, veggies","Pressure cook until soft."),
    ("Paneer Bhurji","Paneer, onion","Crumble paneer. Cook with onion."),
    ("Lemon Rice","Rice, lemon","Mix lemon juice with rice."),
    ("Idli & Sambar","Idli batter","Steam idli. Prepare sambar."),
    ("Vegetable Poha","Poha, peanuts","Cook poha with onion."),
    ("Rajma Rice","Rajma, rice","Cook rajma curry. Serve with rice."),
    ("Stuffed Paratha","Wheat flour, potato","Stuff potato & cook paratha."),
    ("Veg Pulao","Rice, veggies","Cook rice with vegetables."),
    ("Sprouts Salad","Sprouts","Boil sprouts. Add lemon."),
    ("Tomato Soup","Tomato","Boil & blend tomatoes."),
    ("Veg Sandwich","Bread, veggies","Toast with vegetables."),
    ("Masala Oats","Oats, veggies","Cook oats with spices."),
    ("Curd Bowl","Curd, cucumber","Mix curd & veggies."),
    ("Veg Fried Rice","Rice, veggies","Stir fry veggies with rice."),
    ("Paneer Salad","Paneer","Mix paneer & vegetables."),
    ("Veg Soup","Vegetables","Boil vegetables."),
    ("Ragi Porridge","Ragi flour","Cook slowly with water."),
    ("Cabbage Fry","Cabbage","Stir fry lightly."),
    ("Besan Omelette","Besan","Pan cook batter."),
    ("Dal & Chapati","Dal","Serve cooked dal with chapati."),
    ("Veg Cutlet","Vegetables","Mash, shape & shallow fry."),
    ("Bottle Gourd Khichdi","Rice, dal","Cook with lauki."),
    ("Fruit Bowl","Fruits","Chop fruits & serve.")
]

NONVEG_MEALS = [
    ("Egg Omelette","Eggs, onion","Beat eggs & cook."),
    ("Grilled Chicken","Chicken","Grill marinated chicken."),
    ("Fish Curry","Fish","Cook with tomato gravy."),
    ("Boiled Eggs","Eggs","Boil 10 mins."),
    ("Chicken Soup","Chicken","Boil with spices."),
    ("Egg Fried Rice","Rice, egg","Stir fry egg & rice."),
    ("Grilled Fish","Fish","Pan grill."),
    ("Chicken Sandwich","Bread, chicken","Toast sandwich."),
    ("Egg Bhurji","Eggs","Scramble with onion."),
    ("Chicken Pulao","Rice, chicken","Cook together."),
    ("Fish Fry","Fish","Shallow fry."),
    ("Chicken Curry","Chicken","Cook in gravy."),
    ("Egg Curry","Eggs","Cook boiled eggs."),
    ("Chicken Salad","Chicken","Mix with veggies."),
    ("Fish Soup","Fish","Boil lightly."),
    ("Egg Toast","Eggs","Serve on toast."),
    ("Chicken Wrap","Chapati","Wrap chicken."),
    ("Grilled Chicken Veg","Chicken","Grill with veggies."),
    ("Fish Rice Bowl","Fish","Serve with rice."),
    ("Egg Salad","Eggs","Mix chopped eggs."),
    ("Chicken Stir Fry","Chicken","Quick fry."),
    ("Fish Lemon Curry","Fish","Cook with lemon."),
    ("Egg Rice","Eggs","Serve scrambled eggs."),
    ("Chicken Stew","Chicken","Slow cook."),
    ("Fish Stew","Fish","Cook in broth."),
    ("Egg Paratha","Eggs","Cook inside paratha."),
    ("Chicken Cutlet","Chicken","Shallow fry."),
    ("Protein Bowl","Chicken & eggs","Serve together.")
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
