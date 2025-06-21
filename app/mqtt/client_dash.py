
import streamlit as st
import os
import uuid
import time
import paho.mqtt.client as mqtt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# --- Config ---
BROKER = "localhost"
PORT = 1883
TOPIC_PUB = "warl0k/_server"
TOPIC_SUB = "warl0k/_client"
KEY_DIR = "../_session_keys"
os.makedirs(KEY_DIR, exist_ok=True)

# --- Safe Global State ---
mqtt_state = {"payload": None}

# --- Generate and Save Session Key ---
def create_ephemeral_key():
    return AESGCM.generate_key(bit_length=128)

def save_key(session_id, key_bytes):
    with open(os.path.join(KEY_DIR, f"{session_id}.key"), "w") as f:
        f.write(key_bytes.hex())

# --- Encryption ---
def encrypt_payload(key, message):
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, message.encode(), None)
    return nonce, ciphertext

def decrypt_payload(key, nonce, ciphertext):
    aesgcm = AESGCM(key)
    try:
        return aesgcm.decrypt(nonce, ciphertext, None).decode()
    except Exception as e:
        return f"[DECRYPTION ERROR: {type(e).__name__} - {str(e)}]"

# --- MQTT Setup ---
def on_connect(client, userdata, flags, rc):
    client.subscribe(TOPIC_SUB)

def on_message(client, userdata, msg):
    mqtt_state["payload"] = msg.payload  # thread-safe buffer

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)
client.loop_start()

# --- Streamlit UI Setup ---
st.set_page_config("WARL0K Final Client", layout="wide")
st.title("🔐 WARL0K MQTT Client with Session Locking (Final)")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "ephemeral_key" not in st.session_state:
    st.session_state.ephemeral_key = create_ephemeral_key()
    save_key(st.session_state.session_id, st.session_state.ephemeral_key)
if "mqtt_payload" not in st.session_state:
    st.session_state.mqtt_payload = None

# --- Input and Send ---
message = st.text_input("Message to Encrypt & Send", value="AUTH_REQUEST")
if st.button("🚀 Send Message"):
    nonce, ct = encrypt_payload(st.session_state.ephemeral_key, message)
    payload = st.session_state.session_id.encode() + nonce + ct
    client.publish(TOPIC_PUB, payload)
    st.success("Message sent with session ID.")
    st.code(payload.hex())

# --- Show ID & Key ---
st.subheader("🆔 Session ID")
st.code(st.session_state.session_id)
st.subheader("🔑 AES Key (hex)")
st.code(st.session_state.ephemeral_key.hex())

# --- Transfer MQTT payload safely to Streamlit state ---
if mqtt_state["payload"] and st.session_state.mqtt_payload is None:
    st.session_state.mqtt_payload = mqtt_state["payload"]

# --- Show Response if Available ---
if st.session_state.mqtt_payload:
    st.subheader("📥 Received Payload")
    payload = st.session_state.mqtt_payload
    st.code(payload.hex())

    session_id_resp = payload[:36].decode()
    nonce_recv = payload[36:48]
    ct_recv = payload[48:]

    if session_id_resp == st.session_state.session_id:
        decrypted = decrypt_payload(st.session_state.ephemeral_key, nonce_recv, ct_recv)
        st.subheader("🧠 Decrypted Response")
        st.code(decrypted)
    else:
        st.warning("Session ID mismatch — this message is not for this client.")
else:
    st.info("Waiting for server response...")
