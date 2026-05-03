import cv2
import mediapipe as mp

# Screen zones
FRAME_WIDTH = 640
LEFT_ZONE = FRAME_WIDTH // 3
RIGHT_ZONE = (FRAME_WIDTH // 3) * 2

# Distance thresholds (shoulder width in pixels)
TOO_CLOSE = 200
TOO_FAR = 100

with mp.solutions.pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5) as pose:

    cap = cv2.VideoCapture(0)
    cap.set(3, FRAME_WIDTH)

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
            # Draw skeleton
            mp.solutions.drawing_utils.draw_landmarks(
                frame,
                result.pose_landmarks,
                mp.solutions.pose.POSE_CONNECTIONS)

            # Get nose position for left/right detection
            nose = result.pose_landmarks.landmark[0]
            cx = int(nose.x * FRAME_WIDTH)

            # Get shoulder positions for distance detection
            left_shoulder = result.pose_landmarks.landmark[11]
            right_shoulder = result.pose_landmarks.landmark[12]

            left_x = int(left_shoulder.x * FRAME_WIDTH)
            right_x = int(right_shoulder.x * FRAME_WIDTH)

            # Calculate shoulder width in pixels
            shoulder_width = abs(right_x - left_x)

            # Decide left/right command
            if cx < LEFT_ZONE:
                direction = "TURN LEFT"
                dir_color = (255, 0, 0)
            elif cx > RIGHT_ZONE:
                direction = "TURN RIGHT"
                dir_color = (0, 0, 255)
            else:
                direction = "CENTER"
                dir_color = (0, 255, 0)

            # Decide distance command
            if shoulder_width > TOO_CLOSE:
                distance = "TOO CLOSE - STOP"
                dis_color = (0, 0, 255)
            elif shoulder_width < TOO_FAR:
                distance = "TOO FAR - GO FORWARD"
                dis_color = (255, 0, 0)
            else:
                distance = "GOOD DISTANCE"
                dis_color = (0, 255, 0)

            # Show commands on screen
            cv2.putText(frame, direction, (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, dir_color, 3)
            cv2.putText(frame, distance, (50, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, dis_color, 3)
            cv2.putText(frame, f"Shoulder: {shoulder_width}px", (50, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            print(f"Direction: {direction} | Distance: {distance} | Shoulder: {shoulder_width}px")

        else:
            cv2.putText(frame, "NO PERSON - STOP", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            print("No person detected - STOP")

        # Draw zone lines
        cv2.line(frame, (LEFT_ZONE, 0), (LEFT_ZONE, 480), (255, 255, 0), 2)
        cv2.line(frame, (RIGHT_ZONE, 0), (RIGHT_ZONE, 480), (255, 255, 0), 2)

        cv2.imshow("Detection Logic", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()