from queue import Full
import numpy as np
from multiprocessing.synchronize import Event as MultiprocessingEvent

from web_of_cams.camera_frame_buffer import CameraFrameBuffer


# def consumer(
#     camera_info: dict[str, tuple[int, int]],
#     output_folder: str | Path,
#     frame_queue: MultiprocessingQueue,
#     stop_event: MultiprocessingEvent,
#     fps: float = 30.0,
# ):
#     # fourcc = cv2.VideoWriter.fourcc(*"mp4v")

#     # writers = {
#     #     cam_id: cv2.VideoWriter(
#     #         f"{Path(output_folder)}/cam_{cam_id}.mp4", fourcc, fps, frame_size
#     #     )
#     #     for cam_id, frame_size in camera_info
#     # }

#     while True:
#         try:
#             frame_bytes = frame_queue.get(timeout=1)
#             print(frame_bytes[0:10])
#         except Empty:
#             pass

#         if stop_event.is_set() and frame_queue.empty():
#             print("Stopping recording")
#             break

#     # for writer in writers.values():
#     #     writer.release()


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
                print("--------printing from consumer_sm--------")
                print(f"frame from: {cam_buffer.cam_id}")
                print(frame[0, 3, :])
                print(f"shape of frame: {frame.shape}")
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


# Thread Pool Executor doesn't seem to be any faster for two cameras

# def process_frame(cam_buffer: CameraFrameBuffer) -> tuple[np.ndarray, float] | None:
#     if cam_buffer.frame_ready_event.wait(1):
#         cam_buffer.frame_access_sem.acquire()
#         frame = np.ndarray(
#             (cam_buffer.frame_shape[0], cam_buffer.frame_shape[1], 3),
#             dtype=cam_buffer.dtype,
#             buffer=cam_buffer.shm.buf,
#         ).copy()
#         timestamp = np.ndarray(
#             (1,), dtype=np.float64, buffer=cam_buffer.timestamp_mem.buf,
#         ).copy()[0]
#         cam_buffer.frame_access_sem.release()
#         cam_buffer.frame_ready_event.clear()
#         return(frame, timestamp)


# def consumer_sm(camera_frame_buffers: list[CameraFrameBuffer], stop_event: MultiprocessingEvent):
#     timestamps = {cam_buffer.cam_id: [] for cam_buffer in camera_frame_buffers}

#     with ThreadPoolExecutor(max_workers=len(camera_frame_buffers)) as executor:
#         while not stop_event.is_set():
#             # Submit the processing tasks for all cameras to the executor
#             future_to_cam_buffer = {executor.submit(process_frame, cam_buffer): cam_buffer for cam_buffer in camera_frame_buffers}

#             # Iterate over completed tasks
#             for future in as_completed(future_to_cam_buffer):
#                 cam_buffer = future_to_cam_buffer[future]
#                 try:
#                     data = future.result()  # Get the result of the processing
#                     if data:
#                         frame, timestamp = data

#                         print("--------printing from video_recorder_sm--------")
#                         print(f"frame from: {cam_buffer.cam_id}")
#                         print(frame[0, 3, :])
#                         print(f"shape of frame: {frame.shape}")
#                         timestamps[cam_buffer.cam_id].append(timestamp)

#                 except Exception as exc:
#                     print(f'Camera {cam_buffer.cam_id} generated an exception: {exc}')

#         for cam_id, timestamp_list in timestamps.items():
#             if timestamp_list:
#                 # calculate average difference between consecutive timestamps
#                 average_latency = np.mean(np.diff(np.array(timestamp_list))) / 1e9
#                 print(f"Average latency for camera {cam_id}: {average_latency}")
