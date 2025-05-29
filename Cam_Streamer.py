from flask import Flask, render_template, Response
from picamera2 import Picamera2
import cv2
import numpy as np
import time
import threading
from datetime import datetime
import os
import paho.mqtt.client as mqtt

app = Flask(__name__)

picam2 = None
recording = False
video_writer = None
video_lock = threading.Lock()


def initialize_camera():
    global picam2
    if picam2 is None:
        picam2 = Picamera2()
        config = picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)})
        picam2.configure(config)
        picam2.start()
        time.sleep(2)


def generate_frames():
    global picam2, recording, video_writer

    if picam2 is None:
        initialize_camera()

    while True:
        frame = picam2.capture_array()

        with video_lock:
            if recording and video_writer is not None:
                try:
                    bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    video_writer.write(bgr_frame)
                except Exception as e:
                    print(f"[ERROR writing frame]: {e}")

        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')



@app.route('/video_feed/')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


def on_message_1(client, userdata, msg):
    global recording, video_writer

    payload = msg.payload.decode().strip().lower()
    print(f"[MQTT-1 YOLO/result]: {payload}")

    if payload == "is_person" and not recording:
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not os.path.exists("videos"):
            os.makedirs("videos")
        filename = f"videos/record_{now}.avi"
        print(f"[Start Recording] {filename}")
        height, width, _ = picam2.capture_array().shape
        fourcc = cv2.VideoWriter_fourcc(*'XVID')

        with video_lock:
            video_writer = cv2.VideoWriter(filename, fourcc, 20.0, (width, height))
            recording = True

        time.sleep(10)

        print("[End Recording]")
        with video_lock:
            if video_writer:
                video_writer.release()
                video_writer = None
            recording = False 

def on_message_2(client, userdata, msg):
    payload = msg.payload.decode().strip().lower()
    print(f"[MQTT-2 Ysensor/motion]: {payload}")

    if payload == "motion_detective":
        print("Motion Detected!")

def mqtt_thread(broker_ip, topic, on_message_callback):
    client = mqtt.Client()
    client.on_message = on_message_callback
    client.connect(broker_ip, 1883, 60)
    client.subscribe(topic)
    client.loop_forever()

if __name__ == '__main__':
    try:
        initialize_camera()

        threading.Thread(target=mqtt_thread, args=("223.194.166.217", "YOLO/result", on_message_1), daemon=True).start()
        threading.Thread(target=mqtt_thread, args=("223.194.166.218", "sensor/motion", on_message_2), daemon=True).start()

        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        if picam2:
            picam2.stop()
            picam2.close()
