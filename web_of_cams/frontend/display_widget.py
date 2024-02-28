from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton
from PySide6.QtGui import QImage, QPixmap
from multiprocessing import Event

from web_of_cams.camera_frame_buffer import CameraFrameBuffer
from web_of_cams.process_handler import camera_process_handler_sm, shutdown_processes

class DisplayWidget(QWidget):
    def __init__(self, cam_buffers: list[CameraFrameBuffer]):
        super().__init__()

        self.stop_event = Event()

        self.cam_buffers = cam_buffers

        self._layout = QVBoxLayout()

        self.video_display = QLabel(self)
        self.cam_id_label = QLabel(self)
        # self.cam_id_label.setText(f"Camera {cam_buffer.cam_id}")

        self.start_button = QPushButton("Start", self)
        self.start_button.clicked.connect(self.start_processes)

        self.stop_button = QPushButton("Stop", self)
        self.stop_button.clicked.connect(self.stop_processes)
        self.stop_button.setEnabled(False)

        self._layout.addWidget(self.video_display)
        self._layout.addWidget(self.cam_id_label)
        self._layout.addWidget(self.start_button)
        self._layout.addWidget(self.stop_button)

        self.setLayout(self._layout)

        # self.updateframes()

    def start_processes(self):
        self.processes = camera_process_handler_sm(self.cam_buffers, self.stop_event)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_processes(self):
        shutdown_processes(self.processes, self.cam_buffers, self.stop_event)

    # def updateframes(self):
    #     while True:
    #         camid, frame = self.queue.get()
    #         image = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format.Format_RGB888).rgbSwapped()
    #         pixmap = QPixmap.fromImage(image)
    #         self.video_display.setPixmap(pixmap)


class VideoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # Create a spin box for setting the run time
        self.timer_spinbox = QSpinBox(self)
        self.timer_spinbox.setRange(1, 10000)  # set a sensible range
        self.layout.addWidget(self.timer_spinbox)
        
        # Start/Stop button
        self.start_stop_button = QPushButton("Start", self)
        self.start_stop_button.clicked.connect(self.start_stop_clicked)
        self.layout.addWidget(self.start_stop_button)

        self.stop_event = Event()
        self.processes = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.stop_processes)

    def start_stop_clicked(self):
        if self.start_stop_button.text() == "Start":
            # Start the camera processes
            self.start_processes()
            # Change button text
            self.start_stop_button.setText("Stop")
            # Start the timer
            self.timer.start(self.timer_spinbox.value() * 1000)  # convert seconds to milliseconds
        else:
            self.stop_processes()

    def start_processes(self):
        # camera_buffers should be defined and passed here
        self.process_handler = Process(target=camera_process_handler_sm, args=(camera_buffers, self.stop_event))
        self.process_handler.start()
        self.processes.append(self.process_handler)

    def stop_processes(self):
        self.stop_event.set()
        for process in self.processes:
            process.join()
        # Clean up
        for buffer in camera_buffers:
            buffer.cleanup()
        # Reset the GUI elements
        self.start_stop_button.setText("Start")
        self.timer.stop()