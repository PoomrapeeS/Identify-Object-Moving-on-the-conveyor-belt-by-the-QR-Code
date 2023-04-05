## Originally created by Leo
## Edited by SupKCH

from gpiozero import LED

# ENA.on()  => free
# ENA.off() => active
# DIR.on()  => to Front/forward
# DIR.off() => to Back/backward

# Motor driven at 500Hz (0.002 s period) pulsing works fine

class stepper():
    def __init__(self, pulse_pin, direction_pin, enable_pin, delay=0.000001):
        self.PUL = LED(pulse_pin)
        self.DIR = LED(direction_pin)
        self.ENA = LED(enable_pin)
        self.delay = delay
        self.ENA.on()
    
    def forward(self, step=1):
        self.ENA.off()
        self.DIR.on()
        self.PUL.blink(on_time=self.delay, off_time=self.delay, n=step, background=False)
        self.ENA.on()
        self.PUL.off()
        return

    def backward(self, step=1):
        self.ENA.off()
        self.DIR.off()
        self.PUL.blink(on_time=self.delay, off_time=self.delay, n=step, background=False)
        self.ENA.on()
        self.PUL.off()
        return

    def stop(self):
        self.ENA.on()
        self.PUL.off()
        return
