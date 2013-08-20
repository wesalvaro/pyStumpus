"""A simple status application for DigiSparks on Mac (maybe linux?).

sudo /opt/local/bin/port install libusb
export DYLD_LIBRARY_PATH=/opt/local/lib
"""

import sys
import usb
import BaseHTTPServer


REQUEST_TYPE_SEND = usb.util.build_request_type(usb.util.CTRL_OUT,
                                                usb.util.CTRL_TYPE_CLASS,
                                                usb.util.CTRL_RECIPIENT_DEVICE)

REQUEST_TYPE_RECEIVE = usb.util.build_request_type(usb.util.CTRL_IN,
                                                   usb.util.CTRL_TYPE_CLASS,
                                                   usb.util.CTRL_RECIPIENT_DEVICE)

USBRQ_HID_GET_REPORT = 0x01
USBRQ_HID_SET_REPORT = 0x09
USB_HID_REPORT_TYPE_FEATURE = 0x03


def AllSparks():
  sparks = usb.core.find(idVendor=0x16c0, idProduct=0x05df, find_all=True)
  print 'Found %d sparks.' % len(sparks)
  return sparks


class Arduino(object):
  def __init__(self, device):
    self._device = device

  def Write(self, byte):
    self._transfer(REQUEST_TYPE_SEND, USBRQ_HID_SET_REPORT, byte, [])


  def Read(self):
    response = self._transfer(REQUEST_TYPE_RECEIVE, USBRQ_HID_GET_REPORT, 0, 1)
    assert response
    return response[0]


  def _transfer(self, request_type, request, index, value):
    return self._device.ctrl_transfer(
      request_type, request, (USB_HID_REPORT_TYPE_FEATURE << 8) | 0, index,
      value)


class Stumpus(Arduino):
  def __init__(self, device, bad=False, good=False, neutral=False):
    self._bad, self._good, self._neutral = bad, good, neutral
    super(Stumpus, self).__init__(device)

  @property
  def bad(self):
    return self._bad

  @bad.setter
  def bad(self, val):
    self._bad = bool(val)
    self._Status()

  @property
  def good(self):
    return self._good

  @good.setter
  def good(self, val):
    self._good = bool(val)
    self._Status()

  @property
  def neutral(self):
    return self._neutral

  @neutral.setter
  def neutral(self, val):
    self._neutral = bool(val)
    self._Status()

  def _Status(self):
    bad = 'R' if self.bad else ''
    good = 'G' if self.good else ''
    neutral = 'B' if self.neutral else ''
    status = '-%s%s%s' % (bad, good, neutral)
    for c in status:
      self.Write(ord(c))

class StumpusHandler(BaseHTTPServer.BaseHTTPRequestHandler):

  def do_GET(self):
    stumps = tuple(Stumpus(spark) for spark in AllSparks())
    _, index_str, statuses_str = self.path.partition('?')[0].split('/')
    i = int(index_str)
    statuses = statuses_str.split(',')
    try:
      stump = stumps[i]
    except IndexError:
      self.send_response(404)
      self.end_headers()
      raise
    print 'Setting stump %d to %r.' % (i, statuses)

    for status in statuses:
      if status == 'good' or status == 'green':
        stump.good = True
      elif status == 'bad' or status == 'red':
        stump.bad = True
      elif status == 'neutral' or status == 'blue':
        stump.neutral = True
      elif status == 'off':
        stump.good = False
        stump.bad = False
        stump.neutral = False
      else:
        self.send_response(400)
        self.end_headers()
        raise Exception


    self.send_response(200)
    self.end_headers()



def main(unused_argv):
  httpd = BaseHTTPServer.HTTPServer(('', 8000), StumpusHandler)
  try:
    httpd.serve_forever()
  except KeyboardInterrupt:
    pass
  httpd.server_close()


main(sys.argv)

