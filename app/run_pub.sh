##!/bin/bash
#/snap/bin/mosquitto_pub -h localhost -t "warl0k/server" -m "hello from client"
# Example: test encoded payload
#python3 -c 'import os, sys; sys.stdout.buffer.write(os.urandom(12) + b"simulated-response")' \
#| /snap/bin/mosquitto_pub -h localhost -t warl0k/server -s
/snap/bin/mosquitto_pub -h localhost -t warl0k/server -r -m "test-response 2003-10-01 12:00:00 danny"
