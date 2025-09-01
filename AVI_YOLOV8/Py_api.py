import zmq
import cv2
import base64
import threading
from datetime import datetime
import sys
import cv2
import gxipy as gx
import numpy as np
import time
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal, QThread


# inicializa ZeroMQ
context = zmq.Context()
socket = context.socket(zmq.PUB)   # publisher
socket.bind("tcp://*:5555")        # porta 5555

# conecta na câmera Daheng
device_manager = gx.DeviceManager()
device_manager.update_device_list()
cam = device_manager.open_device_by_index(1)
cam.stream_on()
frameagora = None
raw_image = None
b64 = None
frame_bgr = None
frame_all = None
def capturar_frame():
    global cam, frameagora, raw_image   
    while True:
        raw_image = cam.data_stream[0].get_image()
        frameagora = raw_image
def converter_b64():
    global frameagora, b64, raw_image, frame_bgr
    global socket
    global cam

    while True:
        if frameagora is None:
            continue
        frame = frameagora

        rgb_image = raw_image.convert("RGB")

        frame = rgb_image.get_numpy_array()

        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # codifica como JPG
        _, jpg = cv2.imencode(".bmp", frame_bgr)
        b64 = base64.b64encode(jpg).decode("utf-8")
        socket.send_string(b64)
        

threading.Thread(target=capturar_frame, daemon=True).start()
threading.Thread(target=converter_b64, daemon=True).start()




# Interface PyQt5
class CameraViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Viewer Daheng - PyQt5")
        self.label = QLabel("Esperando frame...", self)
        self.label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)


    def update_image(self):
        while True:
            """Atualiza QLabel com o frame recebido"""
            if frameagora is None:
                time.sleep(0.01)
                continue
            # Converte RawImage para NumPy array RGB
            rgb_image = frameagora.convert("RGB")
            frame_np = rgb_image.get_numpy_array()
            h, w, ch = frame_np.shape
            bytes_per_line = ch * w
            qimg = QImage(frame_np.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg).scaled(self.label.size(), Qt.KeepAspectRatio)
            self.label.setPixmap(pixmap)



if __name__ == "__main__":
    # conecta câmera Daheng
    app = QApplication(sys.argv)
    viewer = CameraViewer()
    viewer.show()
    sys.exit(app.exec_())
