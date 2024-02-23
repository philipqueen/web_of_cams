from multiprocessing import Event

from web_of_cams.camera_frame_buffer import CameraFrameBuffer
from web_of_cams.detect_cameras import detect_cameras
from web_of_cams.process_handler import camera_process_handler_sm


def main():
    webcam_info = detect_cameras()
    stop_event = Event()
    camera_buffers: list[CameraFrameBuffer] = []
    for webcam_id, frame_size in webcam_info.items():
        buffer = CameraFrameBuffer(webcam_id, frame_size)
        camera_buffers.append(buffer)
    camera_process_handler_sm(camera_buffers, stop_event)


if __name__ == "__main__":
    main()
