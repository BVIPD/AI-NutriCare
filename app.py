import streamlit as st
import pandas as pd
import joblib
import pdfplumber
import pytesseract
from PIL import Image
import re
import spacy

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="AI-NutriCare",
    page_icon="🥗",
    layout="centered"
)

st.title("🥗 AI-NutriCare")
st.caption("AI-driven Personalized Diet Recommendation System")
st.markdown("---")

# -------------------- LOAD MODELS SAFELY --------------------
@st.cache_resource
def load_spacy():
    return spacy.load("en_core_web_sm")

@st.cache_resource
def load_model():
    return joblib.load("model/lightgbm_model.pkl")

nlp = load_spacy()
model = load_model()

# -------------------- TEXT EXTRACTION (MILESTONE 1) --------------------
def extract_text(uploaded_file):
    ext = uploaded_file.name.split(".")[-1].lower()
    text = ""
    numeric_data = None

    if ext == "pdf":
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

    elif ext in ["png", "jpg", "jpeg"]:
        img = Image.open(uploaded_file)
        text = pytesseract.image_to_string(img)

    elif ext == "txt":
        text = uploaded_file.read().decode("utf-8")

    elif ext == "csv":
        df = pd.read_csv(uploaded_file)
        text = df["doctor_prescription"].iloc[0]
        numeric_data = df.iloc[0]

    return text.strip(), numeric_data

# -------------------- ML PREDICTION (MILESTONE 2) --------------------
def predict_condition(numeric_data):
    features = ["age", "glucose", "cholesterol", "blood_pressure", "bmi"]
    X = pd.DataFrame([{f: numeric_data[f] for f in features}])
    pred = model.predict(X)[0]
    return "Abnormal" if pred == 1 else "Normal"

# -------------------- NLP + DIET LOGIC (MILESTONE 3) --------------------
def generate_diet(text):
    diet = {
        "condition": [],
        "allowed_foods": ["vegetables", "whole grains", "fruits"],
        "restricted_foods": [],
        "diet_plan": [],
        "lifestyle_advice": []
    }

    text = text.lower()

    if "diabetes" in text:
        diet["condition"].append("Diabetes")
        diet["restricted_foods"].append("sugar")
        diet["diet_plan"].append("Follow a diabetic-friendly low sugar diet.")
        diet["lifestyle_advice"].append("Walk daily for 30 minutes.")

    if "cholesterol" in text:
        diet["condition"].append("High Cholesterol")
        diet["restricted_foods"].append("oily food")
        diet["diet_plan"].append("Increase fiber intake and avoid fried foods.")

    if "blood pressure" in text or "hypertension" in text:
        diet["condition"].append("Hypertension")
        diet["restricted_foods"].append("salt")
        diet["diet_plan"].append("Reduce sodium intake.")

    if not diet["condition"]:
        diet["condition"].append("General Health")
        diet["diet_plan"].append("Maintain a balanced diet.")

    return {
        "condition": ", ".join(diet["condition"]),
        "allowed_foods": list(set(diet["allowed_foods"])),
        "restricted_foods": list(set(diet["restricted_foods"])),
        "diet_plan": " ".join(diet["diet_plan"]),
        "lifestyle_advice": " ".join(diet["lifestyle_advice"])
    }

# -------------------- USER INPUT UI --------------------
st.subheader("📄 Upload Medical Report")

uploaded_file = st.file_uploader(
    "Upload PDF / Image / TXT / CSV",
    type=["pdf", "png", "jpg", "jpeg", "txt", "csv"]
)

manual_text = st.text_area(
    "OR paste doctor prescription text",
    height=150
)

process_btn = st.button("🔍 Generate Diet Recommendation")

# -------------------- PIPELINE EXECUTION --------------------
if process_btn:
    if uploaded_file is None and manual_text.strip() == "":
        st.warning("⚠️ Please upload a file or enter text.")
    else:
        st.success("✅ Processing input...")

        if uploaded_file:
            text, numeric_data = extract_text(uploaded_file)
        else:
            text = manual_text
            numeric_data = None

        st.subheader("📝 Extracted Text")
        st.write(text[:1000])

        if numeric_data is not None:
            condition = predict_condition(numeric_data)
            st.subheader("🩺 ML Predicted Health Status")
            st.write(condition)

        diet = generate_diet(text)

        st.subheader("🍽️ Personalized Diet Recommendation")
        st.json(diet)

        st.download_button(
            label="⬇️ Download Diet Plan (JSON)",
            data=pd.Series(diet).to_json(),
            file_name="diet_plan.json",
            mime="application/json"
        )

st.markdown("---")
st.caption("© AI-NutriCare | End-to-End ML + NLP System")
