import sys
import time
import logging
import smbus
import boto.ses
import yaml
import graphiteudp
from ses import ses
from gpio_control import gpio_control

# Read configuration file
cfg = yaml.load(file('local_settings.yml'))

# Setup logging module
numeric_level = getattr(logging, cfg['log']['level'].upper(), None)
if not isinstance(numeric_level, int):
  raise ValueError('Invalid log level: %s' % loglevel)
#logging.basicConfig(level=numeric_level, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', filename='/dev/shm/fan-control.log')
logging.basicConfig(level=numeric_level, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

logging.debug("Config Options: %s" % cfg)

bus = smbus.SMBus(cfg['smbus'])

graphite = graphiteudp.GraphiteUDPClient(cfg['graphite']['host'], prefix = cfg['device_location'].replace(" ","_"))

ses = ses(cfg['aws_key_id'], cfg['aws_secret_key'])
led1 = gpio_control(cfg['led1']['pin'], 0)
led2 = gpio_control(cfg['led2']['pin'], 0)
buzzer = gpio_control(cfg['buzzer']['pin'], 0)

led1.turn_off()
led2.turn_off()
buzzer.turn_off()

last_state = "over"
while True:
  led1.turn_on()
  while True:
    try:
      data = bus.read_i2c_block_data(cfg['temperature_sensor']['i2c_address'], 0)
    except IOError:
      logging.debug("Error getting temperature. Retrying...")
    else:
      break

  msb = data[0]
  lsb = data[1]
  current_temperature_c = (((msb << 8) | lsb) >> 4) * 0.0625
  current_temperature_f = current_temperature_c * 1.8 + 32
  current_temperature = current_temperature_f
  
  logging.debug("Temperature: %s", current_temperature)
  graphite.send("temperature.f", current_temperature_f)
  graphite.send("temperature.c", current_temperature_c)
  led1.turn_off()
  

  if current_temperature < (cfg['temperature_threshold'] - .5) and last_state != "under":
    ses.send_email(
            cfg['from_email_address'],
            cfg['email_addresses'],
            cfg['device_location'],
            current_temperature, 
            cfg['temperature_threshold'], 
            "under"
            )
    if not cfg['buzzer']['disabled']:
      buzzer.turn_on()
    last_state = "under"
  elif current_temperature >= (cfg['temperature_threshold'] + .5) and last_state != "over":
    ses.send_email(
            cfg['from_email_address'],
            cfg['email_addresses'],
            cfg['device_location'],
            current_temperature, 
            cfg['temperature_threshold'], 
            "over"
            )
    buzzer.turn_off()
    last_state = "over"
  
  led2.turn_on() 
  if ses.test(cfg['from_email_address']):
    led2.turn_off() 

  # Capture ctrl+c and send email
  try:
    time.sleep(cfg['sleep_time'])
  except KeyboardInterrupt:
    led1.turn_on()
    led2.turn_on()
    buzzer.turn_off()
    logging.debug("Caught ctrl+c. Sending Email.")
    sys.exit(0)

