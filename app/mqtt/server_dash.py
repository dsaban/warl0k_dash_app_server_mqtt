
import os
import paho.mqtt.client as mqtt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

BROKER = "localhost"
PORT = 1883
TOPIC_SUB = "warl0k/_server"
TOPIC_PUB = "warl0k/_client"
KEY_DIR = "../app/_session_keys"

# --- Load Key by Session ID ---
def load_key(session_id):
    key_path = os.path.join(KEY_DIR, f"{session_id}.key")
    if not os.path.exists(key_path):
        raise FileNotFoundError(f"Key not found for session {session_id}")
    with open(key_path, "r") as f:
        return bytes.fromhex(f.read())

# --- MQTT Handlers ---
def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connected: {rc}")
    client.subscribe(TOPIC_SUB)
    print(f"[MQTT] Subscribed to {TOPIC_SUB}")

def on_message(client, userdata, msg):
    print(f"[MQTT] Message received on {msg.topic}")
    payload = msg.payload
    print(f"[PAYLOAD] Full (hex): {payload.hex()} (len: {len(payload)})")

    if len(payload) < 48:
        print("[!] Payload too short to extract session_id + nonce + ciphertext.")
        return

    try:
        session_id = payload[:36].decode()
        nonce = payload[36:48]
        ciphertext = payload[48:]

        print(f"[SESSION] ID: {session_id}")
        print(f"[NONCE] {nonce.hex()}")
        print(f"[CIPHERTEXT] {ciphertext.hex()}")

        key = load_key(session_id)
        aesgcm = AESGCM(key)
        decrypted = aesgcm.decrypt(nonce, ciphertext, None).decode()

        print(f"[✓] Decrypted Message: {decrypted}")

        # Reply
        response = f"ACK:{decrypted}"
        nonce_out = os.urandom(12)
        ct_out = aesgcm.encrypt(nonce_out, response.encode(), None)
        response_payload = session_id.encode() + nonce_out + ct_out

        client.publish(TOPIC_PUB, response_payload)
        print(f"[→] Encrypted response sent.")
    except Exception as e:
        print(f"[❌] Decryption failed: {type(e).__name__}: {e}")

# --- Run MQTT Client ---
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)
client.loop_forever()
