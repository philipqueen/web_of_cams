import sys
import time
from PySide6.QtWidgets import QApplication
from multiprocessing import Event

from web_of_cams.camera_frame_buffer import CameraFrameBuffer
from web_of_cams.detect_cameras import detect_cameras
from web_of_cams.process_handler import camera_process_handler_sm, shutdown_processes


def setup_cameras() -> list[CameraFrameBuffer]:
    webcam_info = detect_cameras()
    camera_buffers: list[CameraFrameBuffer] = []
    for webcam_id, frame_size in webcam_info.items():
        buffer = CameraFrameBuffer(webcam_id, frame_size)
        camera_buffers.append(buffer)

    return camera_buffers


def main():
    stop_event = Event()

    camera_buffers = setup_cameras()

    processes = camera_process_handler_sm(camera_buffers, stop_event)

    time.sleep(2)
    shutdown_processes(processes, camera_buffers, stop_event)

if __name__ == "__main__":
    main()
