import cv2
import mediapipe as mp
import socket
import time

# ESP32 WiFi settings
ESP32_IP = "10.94.77.100"
ESP32_PORT = 8888

# Connect to ESP32 with retry
print("Connecting to ESP32...")
connected = False
while not connected:
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(5)
        client.connect((ESP32_IP, ESP32_PORT))
        connected = True
        print("Connected to ESP32 via WiFi!")
    except:
        print("Retrying connection...")
        time.sleep(2)

# Screen settings
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
CENTER_X = FRAME_WIDTH // 2

# Distance thresholds
TOO_CLOSE = 200
TOO_FAR = 100
GOOD_DISTANCE = 150

# PID values for direction control
KP = 0.5      # Proportional gain
KI = 0.01     # Integral gain
KD = 0.1      # Derivative gain

# PID variables
prev_error_x = 0
integral_x = 0

# Base speed
BASE_SPEED = 150
MAX_SPEED = 255
MIN_SPEED = 80

# Command timing
last_command = ""
last_time = time.time()

def calculate_pid(error):
    global prev_error_x, integral_x

    # Proportional
    P = KP * error

    # Integral
    integral_x += error
    integral_x = max(-100, min(100, integral_x))
    I = KI * integral_x

    # Derivative
    D = KD * (error - prev_error_x)
    prev_error_x = error

    output = P + I + D
    return output

def send_command(cmd):
    global last_command, last_time
    current_time = time.time()
    if cmd != last_command or (current_time - last_time) > 0.3:
        try:
            client.send((cmd + '\n').encode())
            print(f"Command Sent: {cmd}")
            last_command = cmd
            last_time = current_time
        except:
            print("Send failed!")

with mp.solutions.pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5) as pose:

    cap = cv2.VideoCapture(0)
    cap.set(3, FRAME_WIDTH)
    cap.set(4, FRAME_HEIGHT)

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

            # Get nose position
            nose = result.pose_landmarks.landmark[0]
            cx = int(nose.x * FRAME_WIDTH)

            # Get shoulder width for distance
            left_shoulder = result.pose_landmarks.landmark[11]
            right_shoulder = result.pose_landmarks.landmark[12]
            left_x = int(left_shoulder.x * FRAME_WIDTH)
            right_x = int(right_shoulder.x * FRAME_WIDTH)
            shoulder_width = abs(right_x - left_x)

            # Calculate error from center
            error_x = cx - CENTER_X

            # Calculate PID output
            pid_output = calculate_pid(error_x)

            # Calculate speed based on PID
            turn_speed = int(abs(pid_output))
            turn_speed = max(MIN_SPEED, min(MAX_SPEED, turn_speed))

            # Decide command based on distance first
            if shoulder_width > TOO_CLOSE:
                send_command('S')
                display = "TOO CLOSE - STOP"
                color = (0, 0, 255)

            elif shoulder_width < TOO_FAR:
                send_command(f'F{BASE_SPEED}')
                display = "TOO FAR - GO FORWARD"
                color = (255, 0, 0)

            else:
                # Good distance - use PID for direction
                if abs(error_x) < 50:
                    # Person in center - go forward
                    forward_speed = BASE_SPEED
                    send_command(f'F{forward_speed}')
                    display = f"FORWARD speed:{forward_speed}"
                    color = (0, 255, 0)

                elif pid_output > 0:
                    # Person on right
                    send_command(f'R{turn_speed}')
                    display = f"TURN RIGHT speed:{turn_speed}"
                    color = (0, 0, 255)

                else:
                    # Person on left
                    send_command(f'L{turn_speed}')
                    display = f"TURN LEFT speed:{turn_speed}"
                    color = (255, 0, 0)

            # Draw center line
            cv2.line(frame, (CENTER_X, 0), (CENTER_X, FRAME_HEIGHT),
                    (255, 255, 0), 2)

            # Draw error line
            cv2.line(frame, (CENTER_X, 240), (cx, 240),
                    (0, 255, 255), 2)

            # Show info on screen
            cv2.putText(frame, display, (20, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            cv2.putText(frame, f"Error: {error_x}px", (20, 75),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
            cv2.putText(frame, f"PID: {pid_output:.1f}", (20, 105),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
            cv2.putText(frame, f"Shoulder: {shoulder_width}px", (20, 135),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

        else:
            integral_x = 0
            prev_error_x = 0
            send_command('S')
            cv2.putText(frame, "NO PERSON - STOP", (20, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        cv2.imshow("PID Robot Control", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    send_command('S')
    cap.release()
    cv2.destroyAllWindows()
    client.close()
    print("Disconnected from ESP32!")