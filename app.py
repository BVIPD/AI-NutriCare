import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
import re
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="AI-NutritionalCare",
    page_icon="🥗",
    layout="wide"
)

# ---------------- STYLES ----------------
st.markdown("""
<style>
.card {
    background-color:#f9fafb;
    padding:20px;
    border-radius:15px;
    box-shadow:0 6px 20px rgba(0,0,0,0.1);
    margin-bottom:20px;
}
.week {
    background:#e0f2fe;
    padding:15px;
    border-radius:12px;
    margin-top:20px;
}
.day {
    background:white;
    padding:12px;
    border-radius:10px;
    margin-top:10px;
    border-left:6px solid #22c55e;
}
.recipe {
    background:#ecfeff;
    padding:10px;
    border-radius:8px;
    margin-top:6px;
    font-size:14px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- TITLE ----------------
st.title("🥗 AI-NutritionalCare")
st.caption("AI-driven Personalized Diet Recommendation System")
st.divider()

# ---------------- INPUT ----------------
st.subheader("📄 Upload Medical Report")

uploaded_file = st.file_uploader(
    "Upload PDF / Image / TXT / CSV",
    type=["pdf","png","jpg","jpeg","txt","csv"]
)

patient_pref = st.radio(
    "🍽️ Food Preference",
    ["Vegetarian","Non-Vegetarian"],
    horizontal=True
)

manual_text = st.text_area(
    "OR paste doctor prescription text",
    height=150
)

generate = st.button("✨ Generate Diet Recommendation")

# ---------------- TEXT EXTRACTION ----------------
def extract_text(file):
    ext = file.name.split(".")[-1].lower()
    text = ""

    if ext == "pdf":
        with pdfplumber.open(file) as pdf:
            for p in pdf.pages:
                if p.extract_text():
                    text += p.extract_text() + "\n"

    elif ext in ["png","jpg","jpeg"]:
        try:
            img = Image.open(file)
            text = pytesseract.image_to_string(img)
        except:
            text = ""

    elif ext == "txt":
        text = file.read().decode()

    elif ext == "csv":
        df = pd.read_csv(file)
        text = " ".join(df.astype(str).iloc[0].values)

    return text.strip()

# ---------------- PATIENT NAME ----------------
def extract_patient_name(text):
    match = re.search(r"(patient|name)[:\- ]+([A-Za-z ]+)", text, re.I)
    return match.group(2).strip() if match else "Unknown Patient"

# ---------------- DISEASE DETECTION ----------------
def detect_conditions(text):
    conditions=[]
    t=text.lower()
    if "diabetes" in t: conditions.append("Diabetes")
    if "cholesterol" in t: conditions.append("High Cholesterol")
    if "pressure" in t or "hypertension" in t: conditions.append("Hypertension")
    return conditions or ["General Health"]

# ---------------- MEAL PLANS ----------------
VEG_MEALS = [
("Vegetable Khichdi",
"Rice, moong dal, carrot, beans, turmeric, salt",
"Wash rice & dal. Cook with vegetables, turmeric & water until soft."),

("Chapati & Mixed Veg Sabzi",
"Wheat flour, cabbage, carrot, onion, oil, salt",
"Knead dough. Roll chapati & cook. Stir-fry vegetables with oil."),

("Vegetable Upma",
"Rava, mustard seeds, onion, vegetables, oil",
"Roast rava. Temper mustard seeds. Add veggies, water & rava."),

("Oats Porridge",
"Oats, water/milk, salt",
"Boil water, add oats, cook 5 minutes."),

("Vegetable Pulao",
"Rice, vegetables, spices",
"Cook rice with vegetables and spices."),

("Curd Rice",
"Rice, curd, mustard seeds",
"Mix cooked rice with curd and tempering."),

("Vegetable Soup",
"Vegetables, pepper, salt",
"Boil vegetables and blend lightly.")
]

NON_VEG_MEALS = [
("Boiled Eggs & Toast",
"Eggs, bread",
"Boil eggs for 10 mins. Serve with toast."),

("Grilled Chicken & Rice",
"Chicken, rice, spices",
"Grill chicken. Cook rice separately."),

("Fish Curry & Rice",
"Fish, tomato, spices",
"Cook fish in tomato-based gravy."),

("Egg Omelette",
"Eggs, onion, oil",
"Beat eggs, cook on pan."),

("Chicken Stir Fry",
"Chicken, vegetables",
"Stir fry chicken with vegetables."),

("Fish Fry",
"Fish, oil, spices",
"Shallow fry fish."),

("Chicken Soup",
"Chicken, vegetables",
"Boil chicken with vegetables.")
]

# ---------------- MONTH PLAN ----------------
def generate_month(pref):
    base = VEG_MEALS if pref=="Vegetarian" else NON_VEG_MEALS
    month=[]
    for w in range(4):
        week=[]
        for d in range(7):
            meal = base[(w*7+d)%len(base)]
            week.append(meal)
        month.append(week)
    return month

# ---------------- PDF ----------------
def create_pdf(patient, conditions, pref):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    y=800
    c.setFont("Helvetica-Bold",16)
    c.drawString(40,y,"AI-NutritionalCare Diet Report")
    y-=40
    c.setFont("Helvetica",12)
    c.drawString(40,y,f"Patient: {patient}")
    y-=20
    c.drawString(40,y,f"Medical Conditions: {', '.join(conditions)}")
    y-=30

    plan=generate_month(pref)
    day=1
    for w in range(4):
        c.drawString(40,y,f"Week {w+1}")
        y-=20
        for d in range(7):
            food,ing,steps=plan[w][d]
            c.drawString(50,y,f"Day {day}: {food}")
            y-=15
            c.drawString(60,y,f"Ingredients: {ing}")
            y-=15
            c.drawString(60,y,f"Steps: {steps}")
            y-=20
            day+=1
            if y<100:
                c.showPage()
                y=800
    c.save()
    buf.seek(0)
    return buf

# ---------------- RUN ----------------
if generate:
    text = extract_text(uploaded_file) if uploaded_file else manual_text
    patient = extract_patient_name(text)
    conditions = detect_conditions(text)
    month = generate_month(patient_pref)

    st.divider()
    st.header("📄 Output")

    st.markdown(f"""
    <div class='card'>
    <b>Patient:</b> {patient}<br>
    <b>Medical Condition:</b> {", ".join(conditions)}<br>
    <b>Listing 1:</b> Sample Diet Plan from AI-NutritionalCare
    </div>
    """, unsafe_allow_html=True)

    st.subheader("📆 1-Month Diet Plan (Day-wise with Recipes)")

    day=1
    for w,week in enumerate(month):
        st.markdown(f"<div class='week'><b>Week {w+1}</b>", unsafe_allow_html=True)
        for d,meal in enumerate(week):
            food,ing,steps=meal
            st.markdown(f"""
            <div class='day'>
            <b>Day {day}: {food}</b>
            <div class='recipe'>
            <b>Ingredients:</b> {ing}<br>
            <b>How to cook:</b> {steps}
            </div>
            </div>
            """, unsafe_allow_html=True)
            day+=1
        st.markdown("</div>", unsafe_allow_html=True)

    pdf=create_pdf(patient,conditions,patient_pref)

    st.download_button("⬇️ Download JSON",data=pd.Series({
        "patient":patient,
        "conditions":conditions,
        "preference":patient_pref
    }).to_json(),file_name="diet_plan.json")

    st.download_button("⬇️ Download PDF",data=pdf,file_name=f"{patient}_DietPlan.pdf",mime="application/pdf")

st.caption("© AI-NutritionalCare | Final Deployed System")
