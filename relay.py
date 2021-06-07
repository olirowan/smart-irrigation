import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

# Declaration of the break between the changes of the relay status (in seconds)
delayTime = 1800

# Declaration of the input pin which is connected with the sensor.
# Additional to that, the pullup resistor will be activated.
RELAIS_PIN = 21
GPIO.setup(RELAIS_PIN, GPIO.OUT)
GPIO.output(RELAIS_PIN, False)

try:
    while True:

            GPIO.output(RELAIS_PIN, True) # NO is now connected through

            time.sleep(delayTime)

            GPIO.output(RELAIS_PIN, False) # NC is now connected through

            GPIO.cleanup()

except KeyboardInterrupt:
        GPIO.cleanup()
