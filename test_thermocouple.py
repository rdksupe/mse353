from max6675 import MAX6675
import time

# Pin setup
sck = 5
cs = 23
so = 19

sensor = MAX6675(sck, cs, so)

print("Starting Thermocouple Test...")
while True:
    temp = sensor.read_temp()
    if temp is not None:
        print(f"Temperature: {temp:.2f}°C")
    else:
        print("Error: Thermocouple disconnected!")
    time.sleep(1)
