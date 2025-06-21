
# demo_warl0k_dash_mqtt_all.py

import streamlit as st
import paho.mqtt.client as mqtt
import uuid
import threading
import queue
import time
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# --- Session State Initialization ---
if "response_queue" not in st.session_state:
    st.session_state.response_queue = queue.Queue()
if "ephemeral_key" not in st.session_state:
    st.session_state.ephemeral_key = AESGCM.generate_key(bit_length=128)
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "mqtt_client" not in st.session_state:
    st.session_state.mqtt_client = None
if "threads_started" not in st.session_state:
    st.session_state.threads_started = False

BROKER = "localhost"
PORT = 1883
TOPIC_SUB = "warl0k/server2"
TOPIC_PUB = "warl0k/client2"

# --- Encryption/Decryption Helpers ---
def encrypt_message(key: bytes, plaintext: str):
    aesgcm = AESGCM(key)
    nonce = AESGCM.generate_key(bit_length=128)[:12]
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return nonce, ciphertext

def decrypt_message(key: bytes, nonce: bytes, ciphertext: bytes):
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None).decode()

# --- MQTT Client Callbacks ---
def client_on_message(client, userdata, msg):
    try:
        st.session_state.response_queue.put_nowait(msg.payload)
    except Exception as e:
        print(f"[CLIENT] Error pushing message to queue: {e}")

def server_on_message(client, userdata, msg):
    payload = msg.payload.hex()
    print(f"[SERVER] Payload: {payload}")
    try:
        session_id = bytes.fromhex(payload[:36*2]).decode()
        nonce = bytes.fromhex(payload[36*2:36*2 + 24])
        ciphertext = bytes.fromhex(payload[36*2 + 24:])
        key = st.session_state.ephemeral_key
        decrypted = decrypt_message(key, nonce, ciphertext)
        print(f"[SERVER] ✓ AUTH: {decrypted}")
        # Send back confirmation
        reply_nonce, reply_ct = encrypt_message(key, f"ACK:{decrypted}")
        response_hex = session_id.encode().hex() + reply_nonce.hex() + reply_ct.hex()
        # st.session_state.mqtt_client.publish(TOPIC_SUB, bytes.fromhex(response_hex))
        if st.session_state.mqtt_client:
            st.session_state.mqtt_client.publish(TOPIC_PUB, bytes.fromhex(response_hex))
            st.success("Message sent.")
        else:
            st.warning("MQTT client not yet connected. Please wait a few seconds and try again.")
        
        print(f"[SERVER] → Reply sent to {session_id}")
    except Exception as e:
        print(f"[SERVER] Decryption failed: {e}")

# --- MQTT Threads ---
def start_client():
    client = mqtt.Client()
    client.on_message = client_on_message
    client.connect(BROKER, PORT, 60)
    client.subscribe(TOPIC_SUB)
    client.loop_start()
    st.session_state.mqtt_client = client

def start_server():
    server = mqtt.Client()
    server.on_message = server_on_message
    server.connect(BROKER, PORT, 60)
    server.subscribe(TOPIC_PUB)
    server.loop_start()

if not st.session_state.threads_started:
    threading.Thread(target=start_client, daemon=True).start()
    threading.Thread(target=start_server, daemon=True).start()
    st.session_state.threads_started = True

# --- UI ---
st.set_page_config("WARL0K MQTT AUTH", layout="wide")
if st.session_state.mqtt_client:
    st.sidebar.success("MQTT Client Ready ✅")
else:
    st.sidebar.warning("MQTT Client Not Connected ❌")
st.title("🔐 WARL0K MQTT AUTH Dashboard")
st.sidebar.markdown(f"**Session ID**: `{st.session_state.session_id}`")
st.sidebar.markdown(f"**Ephemeral Key**: `{st.session_state.ephemeral_key.hex()}`")

msg_input = st.text_input("Message to send", "AUTH_REQUEST")
if st.button("Send Message"):
    nonce, ciphertext = encrypt_message(st.session_state.ephemeral_key, msg_input)
    payload = st.session_state.session_id.encode().hex() + nonce.hex() + ciphertext.hex()
    # st.session_state.mqtt_client.publish(TOPIC_PUB, bytes.fromhex(payload))
    if st.session_state.mqtt_client:
        st.session_state.mqtt_client.publish(TOPIC_PUB, bytes.fromhex(payload))
        st.success("Message sent.")
    else:
        st.warning("MQTT client not yet connected. Please wait a few seconds and try again.")
    
    st.success("Message sent.")

st.subheader("📥 Incoming Server Responses")
if not st.session_state.response_queue.empty():
    while not st.session_state.response_queue.empty():
        msg = st.session_state.response_queue.get_nowait()
        try:
            session_id = bytes.fromhex(msg[:36*2].hex()).decode()
            nonce = msg[36:48]
            ciphertext = msg[48:]
            decrypted = decrypt_message(st.session_state.ephemeral_key, nonce, ciphertext)
            st.code(f"[{session_id}] → {decrypted}", language="text")
        except Exception as e:
            st.error(f"[CLIENT] Failed to decrypt response: {e}")
else:
    st.info("No server messages received yet.")
