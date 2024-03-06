from multiprocessing import Process
from multiprocessing.synchronize import Event as MultiprocessingEvent

from web_of_cams.camera_frame_buffer import CameraFrameBuffer

from web_of_cams.record_videos import record_videos
from web_of_cams.run_camera import run_camera_sm
from web_of_cams.consumer import consumer_sm


def camera_process_handler_sm(
    camera_buffers: list[CameraFrameBuffer], fps: float, stop_event: MultiprocessingEvent
) -> list[Process]:
    processes = [] # the order of the processes DOES matter here - we want to join cameras first, consumer second, recorder last - i.e. don't make this a dict

    for buffer in camera_buffers:
        p = Process(
            target=run_camera_sm,
            args=(
                int(buffer.cam_id),
                fps,
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
        args=(camera_buffers, fps, stop_event),
    )
    recording_process.start()
    processes.append(recording_process)

    return processes


def shutdown_processes(
    processes: list[Process],
    camera_buffers: list[CameraFrameBuffer],
    stop_event: MultiprocessingEvent,
):
    print("setting stop event")
    stop_event.set()

    print(f"shutting down processes: {[process.pid for process in processes]}")
    for process in processes:
        process.join()
        print(f"Process {process.pid} joined")
    print("finished shutting down processes")

    print("cleaning up camera buffers")
    for buffer in camera_buffers:
        buffer.cleanup()
