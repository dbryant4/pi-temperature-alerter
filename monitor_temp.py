import sys
import time
import logging
import smbus
import boto.ses
from yaml import load

# Read configuration file
cfg = yaml.load(file('local_settings.yml'))
print cfg
sys.exit(1)

# Setup logging module
numeric_level = getattr(logging, cfg.log_level.upper(), None)
if not isinstance(numeric_level, int):
  raise ValueError('Invalid log level: %s' % loglevel)
#logging.basicConfig(level=numeric_level, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', filename='/dev/shm/fan-control.log')
logging.basicConfig(level=numeric_level, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

bus = smbus.SMBus(cfg['smbus'])

last_state = "over"
while True:
  while True:
    try:
      current_temperature = bus.read_byte(cfg['temperature_sensor']['i2c_address']) * 1.8 + 32
    except IOError:
      logging.debug("Error getting temperature. Retrying...")
    else:
      break

  logging.debug("Temperature: %s", current_temperature)
  if current_temperature < cfg['temperature_threshold'] and last_state != "under":
    send_email_via_ses(current_temperature, "under")
    last_state = "under"

  # Capture ctrl+c and send email
  try:
    time.sleep(cfg['sleep_time'])
  except KeyboardInterrupt:
    logging.debug("Caught ctrl+c. Sending Email.")
    sys.exit(0)

def send_email_via_ses(temperature,state="under"):
  logging.debug("Connecting to AWS.")
  conn = boto.ses.connect_to_region(
           'us-east-1',
           aws_access_key_id = cfg['aws_key_id'],
           aws_secret_access_key = cfg['aws_screct_key'])
  logging.info("Sending \"%s\" email" % state)
  conn.send_email(
                  cfg['from_email_address'],
                  "%s temperature is %s minimum" % (cfg['device_location'], state),
                  "The temperature in %s is %s the minimum temperature of %s" %
                    (cfg['device_location'], state.upper, cfg['temperateu_threshold']),
                  cfg['email_addresses'])
  logging.debug("Email sent.")

def test_ses():
    try:
      led_on()
      conn.verify_email_address('dbryant4@gmail.com')
    except boto.exception.BotoServerError as e:
      print "Address Not Verified or Not Connected"
      led_on()
    else:
      print "Connected and Address Verified"
      led_off()


