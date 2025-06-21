#!/bin/bash
# Navigate to the directory where the script is located
git add .
git commit -m "add new mqtt warl0k demo of server and app client"
it remote add origin git@github.com:dsaban/warl0k_dash_app_server_mqtt.git
git branch -M main
git push -u origin main

