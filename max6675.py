import machine
import time

class MAX6675:
    def __init__(self, sck, cs, so):
        self.sck = machine.Pin(sck, machine.Pin.OUT)
        self.cs = machine.Pin(cs, machine.Pin.OUT)
        self.so = machine.Pin(so, machine.Pin.IN)
        self.cs.value(1)

    def read_temp(self):
        self.cs.value(0)
        time.sleep_us(10)
        
        data = 0
        for i in range(16):
            self.sck.value(1)
            data = (data << 1) | self.so.value()
            self.sck.value(0)
            
        self.cs.value(1)
        
        if data & 0x4: # Bit 2 is high if thermocouple is disconnected
            return None
            
        return (data >> 3) * 0.25
