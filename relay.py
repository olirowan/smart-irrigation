# Needed modules will be imported and configured
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
# Declaration of the break between the changes of the relay status (in seconds)
delayTime = 1800

# Declaration of the input pin which is connected with the sensor. Additional to that, the pullup resistor will be activated.
RELAIS_PIN = 21
GPIO.setup(RELAIS_PIN, GPIO.OUT)
GPIO.output(RELAIS_PIN, False)

print("Sensor-test [press ctrl+c to end]")


# Main program loop
try:
    while True:
            print("Starting watering plants. . .")
            print(" ")
            GPIO.output(RELAIS_PIN, True) # NO is now connected through
            time.sleep(delayTime)
            GPIO.output(RELAIS_PIN, False) # NC is now connected through
            print("Stopping watering plants . . .")
            print(" ")
            GPIO.cleanup()
# Scavenging work after the end of the program
except KeyboardInterrupt:
        GPIO.cleanup()
