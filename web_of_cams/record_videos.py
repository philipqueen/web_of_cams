import cv2
from multiprocessing import Queue as MultiprocessingQueue
from multiprocessing.synchronize import Event as MultiprocessingEvent
from queue import Queue

from web_of_cams.camera_frame_buffer import CameraFrameBuffer

def record_videos(camera_buffers: list[CameraFrameBuffer], stop_event: MultiprocessingEvent):
    frame_length_dict = {
        buffer.cam_id: 0 for buffer in camera_buffers
    }
    while True:
        empty_queues = 0
        for buffer in camera_buffers:
            if not buffer.recording_queue.empty():
                frame, timestamp = buffer.recording_queue.get(timeout=0.5)
                # print("--------printing from record_videos--------")
                # print(f"frame from: {buffer.cam_id}")
                # print(frame[0, 3, :])
                # print(timestamp)
                frame_length_dict[buffer.cam_id] += 1
            else:
                empty_queues += 1

        if empty_queues == len(camera_buffers) and stop_event.is_set():
            print(f"stopping recording")
            for cam_id, frame_length in frame_length_dict.items():
                print(f"frames from {cam_id}: {frame_length}")
            break

    print("out of the while loop")


