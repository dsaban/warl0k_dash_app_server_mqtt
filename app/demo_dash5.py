
import streamlit as st
import uuid
import time
import torch
import random
import string
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

from model import (
    train_secret_regenerator,
    evaluate_secret_regenerator,
    add_noise_to_tensor,
    anomaly_score
)

st.set_page_config("WARL0K Multi-Client Secure Dashboard", layout="wide")
vocab = list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")

def to_tensor(text):
    return torch.tensor([vocab.index(c) for c in text], dtype=torch.long)

def entropy(s):
    from collections import Counter
    from math import log2
    counts = Counter(s)
    probs = [v / len(s) for v in counts.values()]
    return -sum(p * log2(p + 1e-12) for p in probs)

# App State
if "model" not in st.session_state:
    st.session_state.model = None
if "sessions" not in st.session_state:
    st.session_state.sessions = []
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=[
        "timestamp", "client_id", "device", "session_id", "secret", "noisy_input", "regenerated",
        "auth_success", "entropy", "drift", "anomaly", "threat_label"
    ])

# Sidebar Controls
st.sidebar.title("WARL0K Client Session Simulator")
device_profile = st.sidebar.selectbox("Device Profile", ["Sensor A", "PLC Gateway", "RTU Node", "Mobile App"])
client_id = st.sidebar.selectbox("Client ID", ["client-001", "client-002", "client-003", "client-XYZ"])
tamper = st.sidebar.checkbox("🔴 Simulate Tampered Session")

if st.sidebar.button("🚀 Launch Session"):
    session_id = str(uuid.uuid4())
    secret = ''.join(random.choices(vocab, k=16))

    st.sidebar.write("📡 Training...")
    progress_bar = st.sidebar.progress(0)
    for i in range(6):
        time.sleep(0.2)
        progress_bar.progress((i + 1) * 16)

    model = train_secret_regenerator(secret, vocab, epochs=90)
    clean_tensor = to_tensor(secret)
    noise_level = 0.3 if not tamper else 0.9
    noisy = add_noise_to_tensor(clean_tensor, len(vocab), noise_level=noise_level)
    regen = evaluate_secret_regenerator(model, noisy.unsqueeze(1), vocab)

    entropy_score = entropy([vocab[i] for i in noisy.tolist()])
    drift = sum(a != b for a, b in zip(secret, regen)) / len(secret)
    anomaly = anomaly_score(clean_tensor, noisy)
    auth_success = secret == regen

    threat_label = "None"
    if anomaly > 0.6:
        threat_label = "Tampered"
    elif anomaly > 0.3:
        threat_label = "Suspicious"

    st.session_state.sessions.append({
        "client_id": client_id,
        "id": session_id,
        "device": device_profile,
        "secret": secret,
        "noisy": ''.join([vocab[i] for i in noisy.tolist()]),
        "regen": regen,
        "entropy": entropy_score,
        "drift": drift,
        "anomaly": anomaly,
        "auth_success": auth_success,
        "threat_label": threat_label
    })

    st.session_state.history.loc[len(st.session_state.history)] = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "client_id": client_id,
        "device": device_profile,
        "session_id": session_id,
        "secret": secret,
        "noisy_input": ''.join([vocab[i] for i in noisy.tolist()]),
        "regenerated": regen,
        "auth_success": auth_success,
        "entropy": entropy_score,
        "drift": drift,
        "anomaly": anomaly,
        "threat_label": threat_label
    }

    st.sidebar.success("Session completed")

# Sidebar Stats + Trend
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Last Session Stats")
if st.session_state.sessions:
    last = st.session_state.sessions[-1]
    st.sidebar.metric("Entropy", f"{last['entropy']:.3f}")
    st.sidebar.metric("Drift", f"{last['drift']:.2%}")
    st.sidebar.metric("Anomaly", f"{last['anomaly']:.3f}")
    st.sidebar.success("✅ Auth Success" if last["auth_success"] else "❌ Auth Failed")
    st.sidebar.warning(f"Threat: {last['threat_label']}")

if not st.session_state.history.empty:
    st.sidebar.markdown("---")
    st.sidebar.caption("📈 Trends Over Time")
    df = st.session_state.history.copy()
    fig, ax = plt.subplots(figsize=(4, 2))
    ax.plot(df["timestamp"], df["entropy"], label="Entropy", marker="o")
    ax.plot(df["timestamp"], df["anomaly"], label="Anomaly", marker="x")
    ax.plot(df["timestamp"], df["drift"], label="Drift", marker="s")
    ax.set_xticklabels(df["timestamp"], rotation=45, ha="right", fontsize=6)
    ax.legend(fontsize=6)
    fig.tight_layout()
    st.sidebar.pyplot(fig)

# Main Display
st.title("📡 WARL0K Multi-Client Session Insights")

if st.session_state.sessions:
    selected = st.selectbox("Select Session", options=[f"{s['id']} ({s['client_id']})" for s in st.session_state.sessions])
    sess = next(s for s in st.session_state.sessions if s["id"] in selected)

    st.subheader(f"Session ID: {sess['id']} — Device: {sess['device']} — Client: {sess['client_id']}")
    col1, col2 = st.columns(2)
    with col1:
        st.code(sess["secret"], language="text")
        st.caption("Original Secret")
        st.code(sess["noisy"], language="text")
        st.caption("Client Fingerprint (Obfuscated Input)")

    with col2:
        st.code(sess["regen"], language="text")
        st.caption("Denoised / Reconstructed by Server")
        st.success("✅ Authentication Passed" if sess["auth_success"] else "❌ Authentication Failed")
        st.warning(f"Threat Level: {sess['threat_label']}")

    st.markdown("---")
    with st.expander("📜 Session Log Details"):
        st.markdown(f"""
        - **Session ID**: `{sess["id"]}`
        - **Client ID**: `{sess["client_id"]}`
        - **Device**: `{sess["device"]}`
        - **Original Secret**: `{sess["secret"]}`
        - **Noisy Input**: `{sess["noisy"]}`
        - **Regenerated**: `{sess["regen"]}`
        - **Auth**: `{"Success" if sess["auth_success"] else "Failed"}`
        - **Threat Label**: `{sess["threat_label"]}`
        - **Entropy**: `{sess["entropy"]:.3f}`
        - **Drift**: `{sess["drift"]:.2%}`
        - **Anomaly**: `{sess["anomaly"]:.3f}`
        """)

# Session Table
st.subheader("📊 Session Data")
if not st.session_state.history.empty:
    st.dataframe(st.session_state.history.sort_values(by="timestamp", ascending=False), use_container_width=True)
else:
    st.info("No session data available yet.")
