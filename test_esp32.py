import machine
import time

# Pin 2 is the default built-in LED on most ESP32 boards
led = machine.Pin(2, machine.Pin.OUT)

print("Starting connectivity test...")
for i in range(10):
    print(f"Blinking LED {i+1}/10")
    led.value(1)
    time.sleep(0.5)
    led.value(0)
    time.sleep(0.5)

print("Test complete!")
