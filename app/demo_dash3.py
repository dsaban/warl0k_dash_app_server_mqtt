
import streamlit as st
import uuid
import time
import torch
import random
import string
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from model import (
    train_secret_regenerator,
    evaluate_secret_regenerator,
    add_noise_to_tensor,
    anomaly_score
)

# ======================
# Config
# ======================
st.set_page_config("WARL0K Secure MQTT Session Dashboard", layout="wide")
vocab = list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")

def to_tensor(text):
    return torch.tensor([vocab.index(c) for c in text], dtype=torch.long)

def entropy(s):
    from collections import Counter
    from math import log2
    counts = Counter(s)
    probs = [v / len(s) for v in counts.values()]
    return -sum(p * log2(p + 1e-12) for p in probs)

# ======================
# App State
# ======================
if "model" not in st.session_state:
    st.session_state.model = None
if "sessions" not in st.session_state:
    st.session_state.sessions = []
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=[
        "timestamp", "session_id", "secret", "noisy_input", "regenerated",
        "auth_success", "entropy", "drift", "anomaly"
    ])

# ======================
# Sidebar Controls
# ======================
st.sidebar.title("WARL0K Session Controller")

if st.sidebar.button("🔄 Simulate Session"):
    session_id = str(uuid.uuid4())
    secret = ''.join(random.choices(vocab, k=16))

    st.sidebar.write("📡 Training...")
    progress_bar = st.sidebar.progress(0)
    for i in range(6):
        time.sleep(0.2)
        progress_bar.progress((i + 1) * 16)

    model = train_secret_regenerator(secret, vocab, epochs=60)
    clean_tensor = to_tensor(secret)
    noisy = add_noise_to_tensor(clean_tensor, len(vocab), noise_level=0.3)
    regen = evaluate_secret_regenerator(model, noisy.unsqueeze(1), vocab)

    entropy_score = entropy([vocab[i] for i in noisy.tolist()])
    drift = sum(a != b for a, b in zip(secret, regen)) / len(secret)
    anomaly = anomaly_score(clean_tensor, noisy)
    auth_success = secret == regen

    st.session_state.sessions.append({
        "id": session_id,
        "secret": secret,
        "noisy": ''.join([vocab[i] for i in noisy.tolist()]),
        "regen": regen,
        "entropy": entropy_score,
        "drift": drift,
        "anomaly": anomaly,
        "auth_success": auth_success
    })

    st.session_state.history.loc[len(st.session_state.history)] = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "session_id": session_id,
        "secret": secret,
        "noisy_input": ''.join([vocab[i] for i in noisy.tolist()]),
        "regenerated": regen,
        "auth_success": auth_success,
        "entropy": entropy_score,
        "drift": drift,
        "anomaly": anomaly
    }

    st.sidebar.success("Session complete")
    time.sleep(random.uniform(0.3, 1.0))

# ======================
# Sidebar Stats
# ======================
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Latest Session Stats")
if st.session_state.sessions:
    last = st.session_state.sessions[-1]
    st.sidebar.metric("Entropy", f"{last['entropy']:.3f}")
    st.sidebar.metric("Drift", f"{last['drift']:.2%}")
    st.sidebar.metric("Anomaly Score", f"{last['anomaly']:.3f}")
    st.sidebar.success("✅ Auth Success" if last["auth_success"] else "❌ Auth Failed")
else:
    st.sidebar.info("Run a session to see metrics.")

# ======================
# Session Viewer
# ======================
st.title("📡 WARL0K Secure Session Results")

if st.session_state.sessions:
    selected = st.selectbox("Select Session", options=[s["id"] for s in st.session_state.sessions])
    sess = next(s for s in st.session_state.sessions if s["id"] == selected)

    st.subheader(f"Session ID: {selected}")
    col1, col2 = st.columns(2)
    with col1:
        st.code(sess["secret"], language="text")
        st.caption("Original Secret")

        st.code(sess["noisy"], language="text")
        st.caption("Client Fingerprint (Noisy Obfuscated)")

    with col2:
        st.code(sess["regen"], language="text")
        st.caption("Denoised / Reconstructed by Server")

        st.success("✅ Authentication Passed" if sess["auth_success"] else "❌ Authentication Failed")

    # Log Block
    st.markdown("---")
    with st.expander("📜 Session Log Details"):
        st.markdown(f"""
        - **Session ID**: `{sess["id"]}`
        - **Original Secret**: `{sess["secret"]}`
        - **Noisy Obfuscated Input**: `{sess["noisy"]}`
        - **Denoised Regenerated Secret**: `{sess["regen"]}`
        - **Authentication**: `{"Success" if sess["auth_success"] else "Failed"}`
        - **Entropy**: `{sess["entropy"]:.3f}`
        - **Drift**: `{sess["drift"]:.2%}`
        - **Anomaly Score**: `{sess["anomaly"]:.3f}`
        """)

# ======================
# Time-Series Visualization
# ======================
st.subheader("📈 Trend Over Sessions")

if not st.session_state.history.empty:
    df = st.session_state.history.copy()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(df["timestamp"], df["entropy"], label="Entropy", marker="o")
    ax.plot(df["timestamp"], df["drift"], label="Drift", marker="x")
    ax.plot(df["timestamp"], df["anomaly"], label="Anomaly", marker="s")
    ax.set_xticklabels(df["timestamp"], rotation=45, ha="right", fontsize=8)
    ax.legend()
    ax.set_ylabel("Score")
    ax.set_title("Entropy / Drift / Anomaly Over Time")
    st.pyplot(fig)

# ======================
# Export
# ======================
st.subheader("📤 Export Session Data")
if st.button("Download CSV"):
    csv = st.session_state.history.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download", csv, "warl0k_sessions.csv", "text/csv")
