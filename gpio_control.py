import sys
import time
from datetime import datetime
import logging

try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO!  This is probably because you need superuser privileges.  You can achieve this by using 'sudo' to run your script")

class gpio_control:
  """ Simple gpio control class """

  def __init__(self, gpio_pin, min_time_between_state_change=180):
    self.gpio_pin = gpio_pin
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(self.gpio_pin, GPIO.OUT)
    self.on = False
    self.off = True
    self.last_action_time = datetime.fromtimestamp(0)
    self.min_time_between_state_change = min_time_between_state_change
  
  def turn_on(self):
    time_since_last_state_change = datetime.now()-self.last_action_time 
    seconds_since_last_state_change = time_since_last_state_change.total_seconds()
    if self.on:
      logging.debug("GPIO pin %s already on. Doing nothing." % str(self.gpio_pin))
    elif seconds_since_last_state_change >= self.min_time_between_state_change:
      try:
        GPIO.output(self.gpio_pin, True)
        self.last_action_time = datetime.now()
        self.on = True
        self.off = False
      except:
        return 1
    else:
      logging.debug("%s sec since last power on which is less than %s sec. "+
                    "Ignoring request.", seconds_since_last_state_change, 
                    self.min_time_between_state_change)

  def turn_off(self):
    time_since_last_state_change = datetime.now()-self.last_action_time 
    seconds_since_last_state_change = time_since_last_state_change.total_seconds()
    if self.off:
      logging.debug("GPIO Pin %s already off. Doing nothing." % str(self.gpio_pin))
    elif seconds_since_last_state_change >= self.min_time_between_state_change:
      try:
        GPIO.output(self.gpio_pin, False)
        self.last_action_time = datetime.now()
        self.on = False
        self.off = True
      except:
        return 1
    else:
      logging.debug("%s sec since last power off which is less than %s sec. "+
                    "Ignoring request.", seconds_since_last_state_change, 
                    self.min_time_between_state_change)
 
  def is_on(self):
    return self.on

  def is_off(self):
    return self.off
