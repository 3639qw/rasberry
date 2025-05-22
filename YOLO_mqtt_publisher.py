# mqtt_publisher.py
import paho.mqtt.client as mqtt
import time

client = mqtt.Client()
client.connect("127.0.0.1", 1883, 60) # change IP

while True:
	time.sleep(15)
	client.publish("YOLO/result", "is_Person")
	print("MQTT message send")
	time.sleep(600)
