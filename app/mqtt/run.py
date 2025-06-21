import os
import shutil
import subprocess
import time

print("[BOOT] Starting WARL0K demo...")

# --- Ensure required directories ---
os.makedirs("logs", exist_ok=True)
os.makedirs("../_session_keys", exist_ok=True)

# --- Check required executables ---
def check_exec(cmd):
    path = shutil.which(cmd)
    if not path:
        raise FileNotFoundError(f"Executable '{cmd}' not found in PATH.")
    print(f"[✓] {cmd} found at {path}")

check_exec("mosquitto")
check_exec("python3")
check_exec("streamlit")

# --- Check script files ---
assert os.path.exists("server_dash_log.py"), "❌ server_dash_log.py not found"
assert os.path.exists("client_dash_all_data_log.py"), "❌ client_dash_all_data_log.py not found"

# --- Safe subprocess launcher ---
def safe_launch(cmd_list, log_file):
    try:
        subprocess.Popen(
            cmd_list,
            stdout=open(log_file, "w"),
            stderr=subprocess.STDOUT
        )
        print(f"[✓] Launched: {' '.join(cmd_list)}")
    except FileNotFoundError as e:
        print(f"[❌] Launch failed: {e}")

# --- Launch Mosquitto (optional, comment if cloud already runs it) ---
safe_launch(["mosquitto", "-c", "/etc/mosquitto/mosquitto.conf"], "logs/mosquitto.log")

# --- Launch WARL0K Server ---
safe_launch(["python3", "server_dash_log.py"], "logs/server.log")

# --- Delay and Launch Client Dashboard ---
time.sleep(2)
safe_launch(["streamlit", "run", "client_dash_all_data_log.py"], "logs/client_dashboard.log")

print("✅ All services launched. Check 'logs/' for outputs.")
