# ==============================
# AI PHISHING DETECTION SYSTEM
# ALL-IN-ONE FILE
# ==============================
import pandas as pd
import pickle
import re
from urllib.parse import urlparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from flask import Flask, request, jsonify
import streamlit as st
import threading
import requests

# ==============================
# 1. FEATURE EXTRACTION (URL)
# ==============================
def extract_url_features(url):
    features = []
    features.append(len(url))
    features.append(url.count('@'))
    features.append(url.count('-'))
    features.append(1 if "https" in url else 0)
    domain = urlparse(url).netloc
    features.append(len(domain))
    return features

# ==============================
# 2. TRAIN MODEL (AUTO)
# ==============================
def train_model():
    data = {
        "text": [
            "Click here to win money",
            "Meeting at 5 pm",
            "Verify your bank account now",
            "Project discussion tomorrow",
            "Urgent login to your account",
            "Lunch at 2 pm"
        ],
        "label": [1, 0, 1, 0, 1, 0]
    }

    df = pd.DataFrame(data)

    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(df['text'])
    y = df['label']

    model = MultinomialNB()
    model.fit(X, y)

    return model, vectorizer

model, vectorizer = train_model()

# ==============================
# 3. OPTIONAL BERT MODEL
# ==============================
USE_BERT = False

if USE_BERT:
    from transformers import pipeline
    bert_model = pipeline("text-classification")

    def bert_predict(text):
        result = bert_model(text)
        return 1 if "NEGATIVE" in result[0]['label'] else 0

# ==============================
# 4. FLASK API
# ==============================
app = Flask(__name__)

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json['text']

    vec = vectorizer.transform([data])
    ml_pred = model.predict(vec)[0]

    if USE_BERT:
        bert_pred = bert_predict(data)
        final_pred = 1 if (ml_pred + bert_pred) >= 1 else 0
    else:
        final_pred = ml_pred

    return jsonify({
        "prediction": int(final_pred),
        "message": "Phishing" if final_pred == 1 else "Safe"
    })

# Run Flask in background
def run_flask():
    app.run(port=5000)

if "flask_started" not in st.session_state:
    threading.Thread(target=run_flask, daemon=True).start()
    st.session_state.flask_started = True

# ==============================
# 5. STREAMLIT UI
# ==============================
st.title("🔐 AI-Based Phishing Detection System")

user_input = st.text_area("Enter Email or URL")

if st.button("Check"):
    try:
        response = requests.post(
            "http://127.0.0.1:5000/predict",
            json={"text": user_input}
        )

        result = response.json()

        if result["prediction"] == 1:
            st.error("⚠️ Phishing Detected!")
        else:
            st.success("✅ Safe Content")

    except:
        st.warning("⚠️ Server not ready. Please wait a few seconds.")