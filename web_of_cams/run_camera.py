from time import perf_counter_ns
import cv2
import numpy as np
from multiprocessing.synchronize import Event as MultiprocessingEvent
from multiprocessing import Queue as MultiprocessingQueue
from multiprocessing import shared_memory, Process, Event, Semaphore


def run_camera_sm(cam_id, frame_ready_event, frame_access_sem, shm_name, frame_size, timestamp_mem_name, stop_event):
    cap = cv2.VideoCapture(cam_id)
    shm = shared_memory.SharedMemory(name=shm_name)
    frame_buffer = np.ndarray((frame_size[0], frame_size[1], 3), dtype=np.uint8, buffer=shm.buf)
    timestamp_mem = shared_memory.SharedMemory(name=timestamp_mem_name)
    timestamp = np.ndarray((1,), dtype=np.float64, buffer=timestamp_mem.buf)

    for _ in range(10):
        cap.read()

    while not stop_event.is_set():
        ret, frame = cap.read()
        if ret:
            frame_access_sem.acquire()
            np.copyto(frame_buffer, frame)
            np.copyto(timestamp, perf_counter_ns())
            frame_access_sem.release()
            frame_ready_event.set()
            # print("--------printing from run_camera_sm--------")
            # print(f"original frame from: {cam_id}")
            # print(frame[0, 3, :])
            # print(f"shape of frame: {frame.shape}")
        else:
            print(f"failed to read frame from {cam_id}")

    print(f"shutting down camera {cam_id}")
    cap.release()
    shm.close()
    timestamp_mem.close()
