import time
from typing import Optional
import cv2
from datetime import datetime
from multiprocessing.synchronize import Event as MultiprocessingEvent
from queue import Empty

import numpy as np

from web_of_cams.camera_frame_buffer import CameraFrameBuffer


def record_videos(
    camera_buffers: list[CameraFrameBuffer],
    stop_event: MultiprocessingEvent,
    recording_event: Optional[MultiprocessingEvent] = None,
):
    video_framecounts = {buffer.cam_id: 0 for buffer in camera_buffers}
    video_writers = {}
    timestamp_lists = {buffer.cam_id: [] for buffer in camera_buffers}
    blank_frames = {
        buffer.cam_id: np.zeros(
            (buffer.frame_shape[0], buffer.frame_shape[1], 3), dtype=buffer.dtype
        )
        for buffer in camera_buffers
    }
    frame_buffers = {buffer.cam_id: None for buffer in camera_buffers}
    cutoff = int((1 / camera_buffers[0].fps) * 1e9)

    while True:
        if recording_event is not None and recording_event.is_set():
            print(f"recording event is set: {recording_event.is_set()}")
            print("setting up video writers")
            datetime_text = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
            for buffer in camera_buffers:
                writer = cv2.VideoWriter(
                    f"{datetime_text}_cam_{buffer.cam_id}.mp4",
                    cv2.VideoWriter.fourcc(*"mp4v"),
                    30,
                    (buffer.frame_shape[1], buffer.frame_shape[0]),
                )
                video_writers[buffer.cam_id] = writer
            break
        elif stop_event.is_set():
            return
        else:
            time.sleep(0.1)


    while True:
        empty_queues = 0
        for buffer in camera_buffers:
            if frame_buffers[buffer.cam_id] is None:
                try:
                    frame, timestamp = buffer.recording_queue.get(timeout=0.5)
                    frame_buffers[buffer.cam_id] = (frame, timestamp)
                except Empty:
                    empty_queues += 1

        if (
            list(frame_buffers.values()).count(None) == 0
        ):  # only parse frame buffers if we have a candidate from each camera
            min_timestamp = min((timestamp for _, timestamp in frame_buffers.values()))
            for cam_id, (frame, timestamp) in frame_buffers.items():
                if timestamp - min_timestamp <= cutoff:
                    video_writers[cam_id].write(frame)
                    video_framecounts[cam_id] += 1
                    timestamp_lists[cam_id].append(timestamp)
                    frame_buffers[cam_id] = None
                else:
                    video_writers[cam_id].write(blank_frames[cam_id])
                    video_framecounts[cam_id] += 1
                    timestamp_lists[cam_id].append(
                        min_timestamp
                    )  # TODO: figure out how to handle timestamp for blank frames

        if empty_queues > 0 and (stop_event.is_set() or not recording_event.is_set()):
            print(f"stopping recording")
            for cam_id, writer in video_writers.items():
                print(f"video {cam_id} has {video_framecounts[cam_id]} frames")
                writer.release()
            for cam_id, timestamp_list in timestamp_lists.items():
                np.save(
                    f"{datetime_text}_cam_{cam_id}_timestamps.npy",
                    np.array(timestamp_list),
                )
                average_latency = np.nanmean(np.diff(np.array(timestamp_list))) / 1e9
                print(f"Average latency for camera {cam_id}: {average_latency}")
                print(f"Average fps for camera {cam_id}: {1 / average_latency:.2f}")
            break

    print("----record_videos done----")
