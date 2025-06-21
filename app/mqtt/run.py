import os
import subprocess
import time

print("[BOOT] Starting WARL0K demo...")

# Ensure required directories exist
os.makedirs("logs", exist_ok=True)
os.makedirs("../_session_keys", exist_ok=True)

# Optional: Start Mosquitto broker (uncomment if needed)
print("Starting Mosquitto...")
subprocess.Popen(
    ["/snap/bin/mosquitto_pub", "-c"],
    # stdout=open("logs/snap/bin/mosquitto_pub.log", "w"),
    stderr=subprocess.STDOUT
)

# Start WARL0K server process
print("Starting WARL0K server...")
subprocess.Popen(
    ["python3", "server_dash_log.py"],
    stdout=open("logs/server.log", "w"),
    stderr=subprocess.STDOUT
)

# Short delay to let server initialize
time.sleep(2)

# Start WARL0K client dashboard (Streamlit)
print("Starting WARL0K client dashboard...")
subprocess.Popen(
    ["streamlit", "run", "client_dash_all_data_log.py"],
    stdout=open("logs/client_dashboard.log", "w"),
    stderr=subprocess.STDOUT
)

print("All services launched. Check logs/ for output.")
