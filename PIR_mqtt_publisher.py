# mqtt_publisher.py
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import time

PIR_PIN = 17
LED_PIN = 13

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)
GPIO.setup(LED_PIN, GPIO.OUT)

client = mqtt.Client()
client.connect("223.194.166.218", 1883, 60)

try:
	while True:
		if GPIO.input(PIR_PIN):
			GPIO.output(LED_PIN, GPIO.HIGH)
			client.publish("sensor/motion", "motion_detected")
			print("MQTT message send")
			time.sleep(10)
	
except KeyboardInterrupt:
	print("프로그램 종료")

finally:
    GPIO.cleanup()
