import streamlit as st
import pandas as pd
import joblib
import pdfplumber
import pytesseract
from PIL import Image
import re
import spacy
from spacy.cli import download

# -------------------- SETUP --------------------
st.set_page_config(page_title="AI-NutriCare", layout="centered")
st.title("🥗 AI-NutriCare")
st.write("AI-driven Personalized Diet Recommendation System")

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")


# Load trained ML model (Milestone 2)
model = joblib.load("model/lightgbm_model.pkl")


# -------------------- TEXT EXTRACTION (M1) --------------------
def extract_text(uploaded_file):
    text = ""
    ext = uploaded_file.name.split(".")[-1]

    if ext == "pdf":
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""

    elif ext in ["png", "jpg", "jpeg"]:
        img = Image.open(uploaded_file)
        text = pytesseract.image_to_string(img)

    elif ext == "txt":
        text = uploaded_file.read().decode()

    elif ext == "csv":
        df = pd.read_csv(uploaded_file)
        text = df["doctor_prescription"].iloc[0]
        return text, df.iloc[0]

    return text, None

# -------------------- ML PREDICTION (M2) --------------------
def predict_condition(numeric_data):
    features = ["age", "glucose", "cholesterol", "blood_pressure", "bmi"]
    X = pd.DataFrame([numeric_data[f] for f in features]).T
    pred = model.predict(X)[0]
    return "Abnormal" if pred == 1 else "Normal"

# -------------------- NLP + DIET (M3) --------------------
def clean_and_segment(text):
    text = text.lower()
    text = re.sub(r"[^a-zA-Z0-9., ]", "", text)
    doc = nlp(text)
    return [s.text for s in doc.sents]

def generate_diet(text):
    diet = {
        "condition": "",
        "allowed_foods": ["vegetables", "whole grains", "fruits"],
        "restricted_foods": [],
        "diet_plan": "",
        "lifestyle_advice": ""
    }

    if "diabetes" in text:
        diet["condition"] += "Diabetes "
        diet["restricted_foods"].append("sugar")
        diet["diet_plan"] += "Follow diabetic diet. "
        diet["lifestyle_advice"] += "Walk daily. "

    if "cholesterol" in text:
        diet["condition"] += "Cholesterol "
        diet["restricted_foods"].append("oily food")

    if "blood pressure" in text:
        diet["condition"] += "Hypertension "
        diet["restricted_foods"].append("salt")

    if diet["diet_plan"] == "":
        diet["diet_plan"] = "Maintain a balanced diet."

    return diet

# -------------------- UI --------------------
uploaded_file = st.file_uploader(
    "Upload Medical Report (PDF / Image / Text / CSV)",
    type=["pdf", "png", "jpg", "jpeg", "txt", "csv"]
)

if uploaded_file:
    st.success("File uploaded successfully")

    text, numeric_data = extract_text(uploaded_file)

    if numeric_data is not None:
        condition = predict_condition(numeric_data)
        st.subheader("🩺 Predicted Health Condition")
        st.write(condition)

    st.subheader("📄 Extracted Text")
    st.write(text[:800])

    diet = generate_diet(text.lower())

    st.subheader("🍽️ Personalized Diet Recommendation")
    st.json(diet)
