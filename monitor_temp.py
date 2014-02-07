import sys
import time
import logging
import smbus
import boto.ses
import yaml
import graphiteudp
from ses import ses

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

last_state = "over"
while True:
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

  if current_temperature < cfg['temperature_threshold'] and last_state != "under":
    ses.send_email(
            cfg['from_email_address'],
            cfg['email_addresses'],
            cfg['device_location'],
            current_temperature, 
            cfg['temperature_threshold'], 
            "under"
            )
    last_state = "under"
  elif current_temperature > cfg['temperature_threshold'] and last_state != "over":
    ses.send_email(
            cfg['from_email_address'],
            cfg['email_addresses'],
            cfg['device_location'],
            current_temperature, 
            cfg['temperature_threshold'], 
            "over"
            )
    last_state = "over"

  ses.test(cfg['from_email_address'])

  # Capture ctrl+c and send email
  try:
    time.sleep(cfg['sleep_time'])
  except KeyboardInterrupt:
    logging.debug("Caught ctrl+c. Sending Email.")
    sys.exit(0)

