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

        if recording:
            with video_lock:
                if video_writer is not None:
                    bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    video_writer.write(bgr_frame)

        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')



@app.route('/video_feed/')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


def on_message(client, userdata, msg):
    global recording, video_writer

    payload = msg.payload.decode().strip().lower()
    print(f"[MQTT]: {payload}")

    if payload == "start" and not recording:
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not os.path.exists("videos"):
            os.makedirs("videos")
        filename = f"videos/record_{now}.avi"
        print(f"[녹화 시작] {filename}")
        height, width, _ = picam2.capture_array().shape
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        video_writer = cv2.VideoWriter(filename, fourcc, 20.0, (width, height))
        recording = True

    elif payload == "stop" and recording:
        with video_lock:
            print("[녹화 종료]")
            recording = False
            if video_writer:
                video_writer.release()
                video_writer = None


# 🔌 MQTT 클라이언트 스레드 실행
def mqtt_thread():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect("localhost", 1883)
    client.subscribe("cctv/record")
    client.loop_forever()


# 🟢 메인 실행
if __name__ == '__main__':
    try:
        initialize_camera()
        threading.Thread(target=mqtt_thread, daemon=True).start()
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        if picam2:
            picam2.stop()
            picam2.close()
