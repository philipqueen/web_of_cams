import sys
from PySide6.QtWidgets import QApplication, QMainWindow

from web_of_cams.__main__ import setup_cameras
from web_of_cams.camera_frame_buffer import CameraFrameBuffer
from web_of_cams.frontend.display_widget import DisplayWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Web of Cams')
        self.setGeometry(100, 100, 800, 600)
        self.createDisplayWidget()

        self.show()

    def createDisplayWidget(self):
        cam_buffers = setup_cameras()
        self.display_widget = DisplayWidget(cam_buffers=cam_buffers)
        self.setCentralWidget(self.display_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())