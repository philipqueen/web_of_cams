from queue import Full
import numpy as np
from multiprocessing.synchronize import Event as MultiprocessingEvent

from web_of_cams.camera_frame_buffer import CameraFrameBuffer


def consumer_sm(
    camera_frame_buffers: list[CameraFrameBuffer], stop_event: MultiprocessingEvent
):
    timestamps = {cam_buffer.cam_id: [] for cam_buffer in camera_frame_buffers}
    while not stop_event.is_set():
        for cam_buffer in camera_frame_buffers:
            if cam_buffer.frame_ready_event.wait(1):
                cam_buffer.frame_access_sem.acquire()
                frame = np.ndarray(
                    (cam_buffer.frame_shape[0], cam_buffer.frame_shape[1], 3),
                    dtype=cam_buffer.dtype,
                    buffer=cam_buffer.shm.buf,
                ).copy()
                timestamp = np.ndarray(
                    (1,), dtype=np.float64, buffer=cam_buffer.timestamp_mem.buf,
                ).copy()[0]
                cam_buffer.frame_access_sem.release()
                cam_buffer.frame_ready_event.clear()
                # print("--------printing from consumer_sm--------")
                # print(f"frame from: {cam_buffer.cam_id}")
                # print(frame[0, 3, :])
                # print(f"shape of frame: {frame.shape}")
                timestamps[cam_buffer.cam_id].append(timestamp)

                cam_buffer.recording_queue.put((frame, timestamp)) # don't use put_nowait here, because we definitely want to record these frames
                try:
                    cam_buffer.display_queue.put_nowait(frame)
                except Full:
                    pass

    # we need the display queue to be empty in order for the process to join, and don't care if the last frames aren't displayed
    # we need the recording queue to empty itself though, as we can't miss recording frames
    for cam_buffer in camera_frame_buffers:
        cam_buffer.display_queue.close()
        cam_buffer.display_queue.cancel_join_thread()

    for cam_id, timestamp_list in timestamps.items():
            if timestamp_list:
                # calculate average difference between consecutive timestamps
                average_latency = np.mean(np.diff(np.array(timestamp_list))) / 1e9
                print(f"Average latency for camera {cam_id}: {average_latency}")
                print(f"Average fps for camera {cam_id}: {1 / average_latency:.2f}")

    print("----consumer_sm done----")
