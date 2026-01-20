import streamlit as st
import pandas as pd
import pdfplumber
from PIL import Image
import pytesseract
import re
import spacy
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="AI-NutritionalCare",
    page_icon="🥗",
    layout="centered"
)

st.title("🥗 AI-NutritionalCare")
st.caption("AI-driven Personalized Diet Recommendation System")
st.markdown("---")

# -------------------- NLP --------------------
@st.cache_resource
def load_spacy():
    nlp = spacy.blank("en")
    nlp.add_pipe("sentencizer")
    return nlp

nlp = load_spacy()

# -------------------- FOOD + RECIPES --------------------
FOOD_DB = {
    "veg": {
        "breakfast": [
            ("Oats with fruits", "Cook oats in water/milk. Add fruits and nuts."),
            ("Vegetable upma", "Roast rava, cook with vegetables and spices."),
            ("Moong dal chilla", "Soak dal, grind, cook like dosa."),
            ("Idli with sambar", "Steam fermented batter. Serve with sambar.")
        ],
        "lunch": [
            ("Brown rice & vegetables", "Steam rice. Stir-fry vegetables."),
            ("Quinoa salad", "Cook quinoa. Add veggies and olive oil."),
            ("Chapati & paneer curry", "Cook paneer with tomato gravy."),
            ("Vegetable khichdi", "Pressure cook rice, dal & vegetables.")
        ],
        "snack": [
            ("Fruit bowl", "Mix seasonal fruits."),
            ("Sprouts salad", "Steam sprouts, add lemon & salt."),
            ("Roasted nuts", "Dry roast peanuts/almonds."),
            ("Low-fat yogurt", "Serve chilled.")
        ],
        "dinner": [
            ("Vegetable soup", "Boil vegetables, blend lightly."),
            ("Tofu salad", "Grill tofu, mix with veggies."),
            ("Steamed vegetables", "Steam with minimal salt."),
            ("Dal & chapati", "Cook dal, serve with chapati.")
        ]
    },
    "nonveg": {
        "breakfast": [
            ("Egg white omelette", "Cook egg whites with veggies."),
            ("Boiled eggs & toast", "Boil eggs, serve with toast."),
            ("Chicken sandwich", "Grilled chicken + whole wheat bread."),
            ("Vegetable omelette", "Eggs with vegetables.")
        ],
        "lunch": [
            ("Grilled chicken & rice", "Grill chicken, serve with rice."),
            ("Fish curry & brown rice", "Cook fish with spices."),
            ("Chicken salad", "Boiled chicken + veggies."),
            ("Egg curry & chapati", "Boiled eggs in gravy.")
        ],
        "snack": [
            ("Boiled eggs", "Sprinkle pepper."),
            ("Greek yogurt", "Serve chilled."),
            ("Fruit & nuts", "Simple mix."),
            ("Roasted chana", "Dry roast.")
        ],
        "dinner": [
            ("Grilled fish", "Marinate & grill."),
            ("Chicken soup", "Boil chicken with herbs."),
            ("Egg bhurji", "Scramble eggs with veggies."),
            ("Steamed fish & salad", "Steam fish lightly.")
        ]
    }
}

# -------------------- HELPERS --------------------
def extract_patient_name(text):
    patterns = [
        r"patient\s*name\s*[:\-]\s*(.*)",
        r"patient\s*[:\-]\s*(.*)",
        r"name\s*[:\-]\s*(.*)"
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return "Unknown Patient"

def extract_text(file):
    ext = file.name.split(".")[-1].lower()
    text = ""

    if ext == "pdf":
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                if page.extract_text():
                    text += page.extract_text() + "\n"

    elif ext in ["png", "jpg", "jpeg"]:
        try:
            text = pytesseract.image_to_string(Image.open(file))
        except:
            text = "OCR not supported."

    elif ext == "txt":
        text = file.read().decode()

    elif ext == "csv":
        df = pd.read_csv(file)
        text = df.to_string()

    return text

def analyze_conditions(text):
    conditions = []
    if "diabetes" in text.lower():
        conditions.append("Diabetes")
    if "cholesterol" in text.lower():
        conditions.append("High Cholesterol")
    if "hypertension" in text.lower() or "blood pressure" in text.lower():
        conditions.append("Hypertension")
    return conditions or ["General Health"]

def generate_month_plan(food_type):
    plan = {}
    db = FOOD_DB[food_type]

    for week in range(1, 5):
        plan[f"Week {week}"] = {}
        for meal in db:
            item, recipe = db[meal][week % 4]
            plan[f"Week {week}"][meal.capitalize()] = {
                "Food": item,
                "Recipe": recipe
            }
    return plan

def create_pdf(patient, conditions, month_plan):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "AI-NutritionalCare Diet Report")

    y -= 30
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Patient: {patient}")
    y -= 20
    c.drawString(50, y, f"Medical Conditions: {', '.join(conditions)}")

    for week, meals in month_plan.items():
        y -= 30
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, week)

        c.setFont("Helvetica", 10)
        for meal, data in meals.items():
            y -= 15
            c.drawString(60, y, f"{meal}: {data['Food']}")
            y -= 12
            c.drawString(75, y, f"Recipe: {data['Recipe']}")

        if y < 100:
            c.showPage()
            y = height - 50

    c.save()
    buffer.seek(0)
    return buffer

# -------------------- UI --------------------
st.subheader("📄 Upload Medical Report")

food_choice = st.radio("Food Preference", ["Vegetarian", "Non-Vegetarian"])
food_key = "veg" if food_choice == "Vegetarian" else "nonveg"

uploaded_file = st.file_uploader("Upload PDF / Image / TXT / CSV",
                                 type=["pdf", "png", "jpg", "jpeg", "txt", "csv"])
manual_text = st.text_area("OR paste doctor prescription text", height=150)

if st.button("🔍 Generate Diet Recommendation"):
    text = extract_text(uploaded_file) if uploaded_file else manual_text
    patient = extract_patient_name(text)
    conditions = analyze_conditions(text)
    month_plan = generate_month_plan(food_key)

    st.subheader("🧾 Sir-Style Output")
    st.code(f"""
Patient: {patient}
Medical Condition: {", ".join(conditions)}
Listing 1: Sample Diet Plan from AI-NutritionalCare
""")

    st.subheader("📅 1-Month Diet Plan with Recipes")
    for week, meals in month_plan.items():
        st.markdown(f"### {week}")
        for meal, data in meals.items():
            st.write(f"**{meal}:** {data['Food']}")
            st.caption(f"Recipe: {data['Recipe']}")

    # JSON Download
    json_data = {
        "patient": patient,
        "conditions": conditions,
        "monthly_plan": month_plan
    }

    st.download_button(
        "⬇️ Download JSON",
        data=pd.Series(json_data).to_json(),
        file_name=f"{patient}_diet_plan.json",
        mime="application/json"
    )

    # PDF Download
    pdf_file = create_pdf(patient, conditions, month_plan)
    st.download_button(
        "⬇️ Download PDF",
        data=pdf_file,
        file_name=f"{patient}_diet_plan.pdf",
        mime="application/pdf"
    )

st.markdown("---")
st.caption("© AI-NutritionalCare | Internship-Grade Deployed System")
