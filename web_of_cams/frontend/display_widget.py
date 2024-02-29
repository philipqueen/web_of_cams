import time
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt, QTimer
from multiprocessing import Event

from web_of_cams.camera_frame_buffer import CameraFrameBuffer
from web_of_cams.process_handler import camera_process_handler_sm, shutdown_processes


class DisplayWidget(QWidget):
    def __init__(self, cam_buffers: list[CameraFrameBuffer]):
        super().__init__()

        self.stop_event = Event()

        self.cam_buffers = cam_buffers

        self.fetch_frames = False

        self._layout = QVBoxLayout()

        self.cam_displays = {}

        for buffer in self.cam_buffers:
            cam_display = {
                "display_widget": QLabel(self),
                "cam_id": QLabel(self),
                "buffer": buffer,
            }

            self.cam_displays[buffer.cam_id] = cam_display

            cam_display["cam_id"].setText(buffer.cam_id)

            self._layout.addWidget(cam_display["display_widget"])
            self._layout.addWidget(cam_display["cam_id"])

        self.max_image_height = super().size().height() // 3
        self.max_image_width = int(super().size().width())

        self.start_button = QPushButton("Start", self)
        self.start_button.clicked.connect(self.start_processes)

        self.stop_button = QPushButton("Stop", self)
        self.stop_button.clicked.connect(self.stop_processes)
        self.stop_button.setEnabled(False)

        self._layout.addWidget(self.start_button)
        self._layout.addWidget(self.stop_button)

        self.setLayout(self._layout)

    def start_processes(self):
        self.processes = camera_process_handler_sm(self.cam_buffers, self.stop_event)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        self.fetch_frames = True
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frames)
        self.timer.start(33)

    def stop_processes(self):
        print("stopping processes")
        self.timer.stop()
        shutdown_processes(self.processes, self.cam_buffers, self.stop_event)
        self.stop_button.setEnabled(False)
        print("finished stopping processes")

    def update_frames(self):
        for display in self.cam_displays.values():
            if not display["buffer"].display_queue.empty():
                cam_id, frame = display["buffer"].display_queue.get()
                image = QImage(
                    frame.data,
                    frame.shape[1],
                    frame.shape[0],
                    QImage.Format.Format_RGB888,
                ).rgbSwapped()
                pixmap = QPixmap.fromImage(image)
                pixmap = pixmap.scaled(
                    self.max_image_width,
                    self.max_image_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                )
                display["display_widget"].setPixmap(pixmap)
