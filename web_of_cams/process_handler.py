import multiprocessing
import time

from multiprocessing import Event, Process
from multiprocessing.synchronize import Event as MultiprocessingEvent

import numpy as np
from web_of_cams.camera_frame_buffer import CameraFrameBuffer

from web_of_cams.detect_cameras import detect_cameras
from web_of_cams.record_videos import record_videos
from web_of_cams.run_camera import run_camera, run_camera_sm
from web_of_cams.consumer import consumer_sm


# def camera_process_handler():
#     webcam_info = (
#         detect_cameras()
#     )  # TODO: Some way to decide which cameras run, other camera parameters
#     stop_event = multiprocessing.Event()
#     recording_queue = multiprocessing.Queue()
#     processes = []
#     recorder = multiprocessing.Process(
#         target=consumer,
#         args=(
#             webcam_info,
#             "output",
#             recording_queue,
#             stop_event,
#             30.0,
#         ),
#     )
#     recorder.start()
#     processes.append(recorder)

#     for webcam_id in webcam_info.keys():
#         p = multiprocessing.Process(
#             target=run_camera, args=(int(webcam_id), recording_queue, stop_event)
#         )
#         p.start()
#         processes.append(p)

#     time.sleep(3)
#     stop_event.set()

#     for process in processes:
#         process.join()


def camera_process_handler_sm(
    camera_buffers: list[CameraFrameBuffer], stop_event: MultiprocessingEvent
) -> list[Process]:
    processes = []

    for buffer in camera_buffers:
        p = Process(
            target=run_camera_sm,
            args=(
                int(buffer.cam_id),
                buffer.frame_ready_event,
                buffer.frame_access_sem,
                buffer.shm.name,
                buffer.frame_shape,
                buffer.timestamp_mem.name,
                stop_event,
            ),
        )
        p.start()
        processes.append(p)

    consumer_process = Process(
        target=consumer_sm,
        args=(camera_buffers, stop_event),
    )
    consumer_process.start()
    processes.append(consumer_process)

    recording_process = Process(
        target=record_videos,
        args=(camera_buffers, stop_event),
    )
    recording_process.start()
    processes.append(recording_process)

    return processes


def shutdown_processes(
    processes: list[Process],
    camera_buffers: list[CameraFrameBuffer],
    stop_event: MultiprocessingEvent,
):
    stop_event.set()

    for process in processes:
        process.terminate()

    for buffer in camera_buffers:
        buffer.cleanup()
