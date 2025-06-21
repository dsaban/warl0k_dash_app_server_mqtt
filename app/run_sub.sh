#mosquitto_sub -h test.mosquitto.org -t warl0k/client
#mosquitto_pub -h test.mosquitto.org -t warl0k/server -m "<12-byte-nonce + encrypted-response>"
/snap/bin/mosquitto_sub -h localhost -t "warl0k/server"
