import cv2

cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame_bytes = frame.tobytes()

    if cv2.waitKey(1) == ord("q"):
        break
    
cap.release()