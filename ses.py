import sys
import time
import logging
import boto.ses

class ses:
  """ Simple wrapper class around boto.ses """

  def __init__(self,aws_key_id, aws_secret_key, region='us-east-1'):
    self.aws_key_id = aws_key_id
    self.aws_secret_key = aws_secret_key
    self.region = region
    self.connect()

  def connect(self):
    self.conn = boto.ses.connect_to_region(
                  self.region,
                  aws_access_key_id=self.aws_key_id,
                  aws_secret_access_key=self.aws_secret_key
                )

  def send_email(self, from_addr, to_addrs, device_location, temperature, threshold, state):
    self.conn.send_email(
                  from_addr,
                  "%s temperature is %s minimum" % (device_location, state),
                  "The temperature in %s is %s which is %s the minimum temperature of %s" %
                    (device_location, str(temperature), state.upper(), threshold),
                  to_addrs)

  def test(self, verified_email_address):
    try:
      res = self.conn.list_verified_email_addresses()
    except boto.exception.BotoServerError as e:
      return False
    except:
      e = sys.exc_info()[0]
      logging.error("Unexpected error: %s" % e)
      return False
    verified_email_addresses = res['ListVerifiedEmailAddressesResponse']['ListVerifiedEmailAddressesResult']['VerifiedEmailAddresses'] 
    if verified_email_address in verified_email_addresses:
      return True
    else:
      return False



