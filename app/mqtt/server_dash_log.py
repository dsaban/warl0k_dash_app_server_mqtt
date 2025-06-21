import os
import logging
import paho.mqtt.client as mqtt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# --- Config ---
BROKER = "localhost"
PORT = 1883
TOPIC_SUB = "warl0k/_server"
TOPIC_PUB = "warl0k/_client"
KEY_DIR = "../_session_keys"
LOG_FILE = "logs/server.log"

# --- Setup Logging ---
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logging.info("🔐 WARL0K Server initializing...")

# --- Load Key by Session ID ---
def load_key(session_id):
    key_path = os.path.join(KEY_DIR, f"{session_id}.key")
    if not os.path.exists(key_path):
        raise FileNotFoundError(f"Key not found for session {session_id}")
    with open(key_path, "r") as f:
        return bytes.fromhex(f.read())

# --- MQTT Handlers ---
def on_connect(client, userdata, flags, rc):
    logging.info(f"[MQTT] Connected with result code {rc}")
    client.subscribe(TOPIC_SUB)
    logging.info(f"[MQTT] Subscribed to {TOPIC_SUB}")

def on_message(client, userdata, msg):
    logging.info(f"[MQTT] Message received on topic '{msg.topic}'")
    payload = msg.payload
    logging.info(f"[PAYLOAD] (hex): {payload.hex()} (len: {len(payload)})")

    if len(payload) < 48:
        logging.warning("Payload too short: cannot extract session ID + nonce + ciphertext.")
        return

    try:
        session_id = payload[:36].decode()
        nonce = payload[36:48]
        ciphertext = payload[48:]

        logging.info(f"[SESSION] ID: {session_id}")
        logging.info(f"[NONCE] {nonce.hex()}")
        logging.info(f"[CIPHERTEXT] {ciphertext.hex()}")

        key = load_key(session_id)
        aesgcm = AESGCM(key)
        decrypted = aesgcm.decrypt(nonce, ciphertext, None).decode()

        logging.info(f"[✓] Decrypted Message: {decrypted}")

        # Reply
        response = f"ACK:{decrypted}"
        nonce_out = os.urandom(12)
        ct_out = aesgcm.encrypt(nonce_out, response.encode(), None)
        response_payload = session_id.encode() + nonce_out + ct_out

        client.publish(TOPIC_PUB, response_payload)
        logging.info(f"[→] Encrypted response sent to {TOPIC_PUB}")

    except Exception as e:
        logging.error(f"[❌] Decryption failed: {type(e).__name__} - {e}")

# --- Run MQTT Server Loop ---
try:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    logging.info("MQTT client initialized, entering loop.")
    client.loop_forever()
except Exception as e:
    logging.critical(f"[FATAL] Server crashed: {type(e).__name__} - {e}")
