import Jetson.GPIO as GPIO
import time

led_pin=11

GPIO.setmode(GPIO.BOARD)
GPIO.setup(led_pin, GPIO.OUT)

try:
    while True:
            GPIO.output(led_pin, GPIO.HIGH)
            time.sleep(0.5)
            
            GPIO.output(led_pin, GPIO.LOW)
            time.sleep(0.5)
except KeyboardInterrupt:
    pass

finally:
    GPIO.cleanup()