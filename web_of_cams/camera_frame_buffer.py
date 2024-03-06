import numpy as np

from multiprocessing import shared_memory, Event, Semaphore, Queue


class CameraFrameBuffer:
    def __init__(self, cam_id: str, frame_shape: tuple):
        self.cam_id = cam_id
        self.frame_shape = frame_shape
        self.dtype = np.uint8
        self.size = frame_shape[0] * frame_shape[1] * 3 * np.dtype(self.dtype).itemsize
        self.shm = shared_memory.SharedMemory(create=True, size=int(self.size))
        self.timestamp_mem = shared_memory.SharedMemory(create=True, size=np.dtype(np.float64).itemsize)
        self.frame_ready_event = Event()
        self.frame_access_sem = Semaphore(1)
        self.recording_queue = Queue()
        self.display_queue = Queue(maxsize=3) # TODO: we might not need each camera to have its own display queue

    def cleanup(self):
        self.shm.close()
        self.shm.unlink()
        self.timestamp_mem.close()
        self.timestamp_mem.unlink()