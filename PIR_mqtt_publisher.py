# mqtt_publisher.py
import paho.mqtt.client as mqtt
import time

client = mqtt.Client()
client.connect("127.0.0.1", 1883, 60)

while True:
	time.sleep(15)
	client.publish("sensor/motion", "motion_detected")
	print("MQTT message send")
	time.sleep(600)
