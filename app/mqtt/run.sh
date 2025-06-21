#!/bin/bash
echo "[BOOT] Starting WARL0K demo..."
# Activate the Python environment (adjust path if needed)
#source venv/bin/activate

mkdir -p logs
mkdir -p ../_session_keys

# Start the MQTT server (optional: only if you want to start mosquito manually)
# echo "Starting Mosquitto..."
# nohup mosquitto -c mosquitto.conf > logs/mosquitto.log 2>&1 &

# Start the WARL0K server process
echo "Starting WARL0K server..."
nohup python3 server_dash_log.py > logs/server.log 2>&1 &

# Start the WARL0K client dashboard (Streamlit)
echo "Starting WARL0K client dashboard..."
#nohup streamlit run client_dash_all_data.py > logs/client_dashboard.log 2>&1 &
nohup streamlit run client_dash_all_data_log.py > logs/client_dashboard.log 2>&1 &
echo "All services launched. Check logs/ for output."
