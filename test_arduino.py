import serial
import time

# Connect to Arduino on COM3
arduino = serial.Serial('COM3', 9600, timeout=1)
time.sleep(2)  # Wait for Arduino to be ready

print("Connected to Arduino!")

# Test all commands
print("Sending F - Forward")
arduino.write(b'F')
time.sleep(2)

print("Sending S - Stop")
arduino.write(b'S')
time.sleep(2)

print("Sending L - Left")
arduino.write(b'L')
time.sleep(2)

print("Sending S - Stop")
arduino.write(b'S')
time.sleep(2)

print("Sending R - Right")
arduino.write(b'R')
time.sleep(2)

print("Sending S - Stop")
arduino.write(b'S')

arduino.close()
print("Test Done!")