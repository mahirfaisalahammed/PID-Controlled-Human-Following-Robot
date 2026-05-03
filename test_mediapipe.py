import cv2
import mediapipe as mp

# New way for mediapipe 0.10.13+
with mp.solutions.pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5) as pose:

    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        result = pose.process(rgb)
        rgb.flags.writeable = True

        frame = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

        if result.pose_landmarks:
            mp.solutions.drawing_utils.draw_landmarks(
                frame,
                result.pose_landmarks,
                mp.solutions.pose.POSE_CONNECTIONS)
            print("Person Detected!")

        cv2.imshow("MediaPipe Test", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    