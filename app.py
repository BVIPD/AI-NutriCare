import streamlit as st
import pandas as pd
import pdfplumber
from PIL import Image
import pytesseract
import re
import json
from io import BytesIO

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="AI-NutritionalCare",
    page_icon="🥗",
    layout="wide"
)

# ---------- CUSTOM UI (LIGHT + GRADIENT + CARDS) ----------
st.markdown("""
<style>
body {
    background: linear-gradient(120deg, #fdfbfb 0%, #ebedee 100%);
}
.main {
    background: transparent;
}
.card {
    background: white;
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0px 10px 25px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}
.header {
    font-size: 36px;
    font-weight: 800;
}
.sub {
    color: #555;
}
.week {
    background: #f7f9fc;
    padding: 15px;
    border-radius: 12px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ---------- TITLE ----------
st.markdown('<div class="header">🥗 AI-NutritionalCare</div>', unsafe_allow_html=True)
st.markdown('<div class="sub">AI-driven Personalized Diet Recommendation System</div>', unsafe_allow_html=True)
st.markdown("---")

# ---------- INPUT CARD ----------
st.markdown('<div class="card">', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "📄 Upload Medical Report (PDF / Image / TXT / CSV)",
    type=["pdf", "png", "jpg", "jpeg", "txt", "csv"]
)

food_pref = st.radio(
    "🥦 Food Preference",
    ["Vegetarian", "Non-Vegetarian"],
    horizontal=True
)

manual_text = st.text_area(
    "OR paste doctor prescription text",
    height=150
)

generate = st.button("✨ Generate Diet Recommendation")

st.markdown('</div>', unsafe_allow_html=True)

# ---------- HELPERS ----------
def extract_text(file):
    ext = file.name.split(".")[-1].lower()
    text = ""

    if ext == "pdf":
        with pdfplumber.open(file) as pdf:
            for p in pdf.pages:
                if p.extract_text():
                    text += p.extract_text()

    elif ext in ["png", "jpg", "jpeg"]:
        try:
            text = pytesseract.image_to_string(Image.open(file))
        except:
            text = ""

    elif ext == "txt":
        text = file.read().decode()

    elif ext == "csv":
        df = pd.read_csv(file)
        text = " ".join(df.astype(str).values.flatten())

    return text.lower()

def extract_patient_name(text):
    m = re.search(r"patient[:\- ]+([a-z ]+)", text, re.I)
    return m.group(1).title() if m else "Unknown Patient"

def extract_conditions(text):
    cond = []
    if "diabetes" in text: cond.append("Diabetes")
    if "cholesterol" in text: cond.append("High Cholesterol")
    if "hypertension" in text or "blood pressure" in text: cond.append("Hypertension")
    return cond if cond else ["General Health"]

# ---------- FULL 7-DAY MEALS ----------
VEG_MEALS = [
("Vegetable Upma","Wash vegetables. Roast semolina. Cook with mustard seeds, onion, vegetables and water."),
("Oats Porridge","Boil oats in water. Add salt, vegetables and cook till soft."),
("Idli & Sambar","Steam idli batter. Cook lentils with vegetables and spices for sambar."),
("Poha","Wash flattened rice. Saute onion, peanuts, turmeric. Mix poha and steam."),
("Dosa","Ferment batter. Pour on pan. Cook until crisp."),
("Vegetable Pulao","Cook rice with mixed vegetables and spices."),
("Curd Rice","Mix cooked rice with curd, add salt and mustard seasoning.")
]

NONVEG_MEALS = [
("Egg Omelette","Beat eggs with onion and salt. Cook on pan."),
("Grilled Chicken","Marinate chicken. Grill till cooked."),
("Fish Curry","Cook fish with onion, tomato and spices."),
("Boiled Eggs","Boil eggs for 10 minutes."),
("Chicken Stir Fry","Cook chicken with vegetables and spices."),
("Egg Bhurji","Scramble eggs with onion and tomato."),
("Fish Grill","Marinate fish. Shallow fry.")
]

def build_month_plan(is_veg):
    base = VEG_MEALS if is_veg else NONVEG_MEALS
    plan = {}
    idx = 0

    for w in range(1,5):
        plan[f"Week {w}"] = {}
        for d in range(1,8):
            meal, recipe = base[idx % 7]
            plan[f"Week {w}"][f"Day {d}"] = {
                "Breakfast": meal,
                "Lunch": meal,
                "Snack": "Fruits / Nuts",
                "Dinner": meal,
                "Recipe": recipe
            }
            idx += 1
    return plan

# ---------- MAIN ----------
if generate:
    if not uploaded_file and not manual_text.strip():
        st.warning("Please upload a file or paste text")
    else:
        text = extract_text(uploaded_file) if uploaded_file else manual_text.lower()
        patient = extract_patient_name(text)
        conditions = extract_conditions(text)

        plan = build_month_plan(food_pref == "Vegetarian")

        # ---------- OUTPUT ----------
        st.markdown("## 📋 Output")

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.write(f"**Patient:** {patient}")
        st.write(f"**Medical Condition:** {', '.join(conditions)}")
        st.write("**Listing 1:** Sample Diet Plan from AI-NutritionalCare")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("## 📆 1-Month Diet Plan (Day-wise with Recipes)")

        for week, days in plan.items():
            with st.expander(week, expanded=False):
                for day, meals in days.items():
                    st.markdown(f"### {day}")
                    st.write(f"🍳 **Breakfast:** {meals['Breakfast']}")
                    st.write(f"🍛 **Lunch:** {meals['Lunch']}")
                    st.write(f"🍎 **Snack:** {meals['Snack']}")
                    st.write(f"🥗 **Dinner:** {meals['Dinner']}")
                    st.info(f"👩‍🍳 **How to cook:** {meals['Recipe']}")

        # ---------- DOWNLOAD ----------
        diet_json = {
            "patient": patient,
            "conditions": conditions,
            "food_preference": food_pref,
            "plan": plan
        }

        st.download_button(
            "⬇️ Download JSON",
            data=json.dumps(diet_json, indent=2),
            file_name=f"{patient}_DietPlan.json"
        )

        st.success("🎉 Diet Plan Generated Successfully!")
