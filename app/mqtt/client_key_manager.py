
import os
import uuid
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY_DIR = "_session_keys"
os.makedirs(KEY_DIR, exist_ok=True)

def generate_session_id():
    return str(uuid.uuid4())

def create_ephemeral_key():
    return AESGCM.generate_key(bit_length=128)

def save_key(session_id, key_bytes):
    with open(os.path.join(KEY_DIR, f"{session_id}.key"), "w") as f:
        f.write(key_bytes.hex())

def load_key(session_id):
    key_path = os.path.join(KEY_DIR, f"{session_id}.key")
    if not os.path.exists(key_path):
        raise FileNotFoundError(f"Key not found for session {session_id}")
    with open(key_path, "r") as f:
        return bytes.fromhex(f.read())

def list_sessions():
    return [f.replace(".key", "") for f in os.listdir(KEY_DIR) if f.endswith(".key")]

if __name__ == "__main__":
    session_id = generate_session_id()
    key = create_ephemeral_key()
    save_key(session_id, key)
    print(f"New session: {session_id}")
    print(f"Key: {key.hex()}")
    print(f"Saved to: {os.path.join(KEY_DIR, f'{session_id}.key')}")
