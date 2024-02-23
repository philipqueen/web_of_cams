import cv2
import numpy as np


CAM_CHECK_NUM = 20
MAX_UNUSED_PORTS = 5


def detect_cameras() -> dict[str, tuple[int, int]]:
    """
    Finds available webcams and returns them as a dict with port as key and frame size as value.
    """
    webcams = dict()
    unused_ports = 0
    for cam_id in range(CAM_CHECK_NUM):
        if unused_ports >= MAX_UNUSED_PORTS:
            break

        cap = cv2.VideoCapture(cam_id)
        if cap is None or not cap.isOpened():
            unused_ports += 1
            continue

        ret, frame = cap.read()
        if not ret:
            unused_ports += 1
            continue

        if frame is None:
            unused_ports += 1
            continue

        ret, frame2 = cap.read()
        if np.mean(frame2) > 10 and np.array_equal(frame, frame2):
            unused_ports += 1
            print(
                f"Camera {cam_id} returned identical non-null frames, skipping as likely virtual camera."
            )
            continue
        webcams[str(cam_id)] = (frame.shape[0], frame.shape[1])
        cap.release()
        del cap
    print(f"Found webcams at following ports: {webcams}")
    return webcams


if __name__ == "__main__":
    print(detect_cameras())
