from flask import Flask, render_template, Response
import cv2
import time, math
import config
import imutils, cv2, os, time
from detect import detect_people, draw_people, draw_metrics
from imutils.video import VideoStream, FPS
from flask import jsonify, stream_with_context

app = Flask(__name__)


def gen_frames():
    labelsPath = os.path.sep.join([config.MODEL_PATH, "coco.names"])
    LABELS = open(labelsPath).read().strip().split("\n")

    weightsPath = os.path.sep.join([config.MODEL_PATH, config.WEIGHTS])
    configPath = os.path.sep.join([config.MODEL_PATH, config.CFG])

    net = cv2.dnn.readNetFromDarknet(configPath, weightsPath)

    if config.USE_GPU:
        print("[INFO] Using GPU")
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
    else:
        print("[INFO] Using CPU")
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

    ln = net.getLayerNames()
    ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]

    cap = cv2.VideoCapture("videos/test.mp4")
    fps = FPS().start()

    while True:
        success, frame = cap.read()
        if not success:
            break
        frame = imutils.resize(frame, width=700, height=700)
        results, no_of_people = detect_people(frame, net, ln, personIdx=LABELS.index("person"))
        violations = draw_people(frame, results)
        draw_metrics(frame, violations, no_of_people)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield "{\"violations\": %d}" % len(violations)
        yield b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
        # time.sleep(0.1)
        fps.update()
    fps.stop()
    print("----------------------------")
    print("[INFO] Elapsed time: {:.2f}".format(fps.elapsed()))
    print("[INFO] Approx. FPS: {:.2f}".format(fps.fps()))


@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
