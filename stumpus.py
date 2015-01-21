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


class Spark(object):

  @classmethod
  def All(cls):
    id_vendor, id_product = 0x16c0, 0x05df
    return [cls(x) for x in usb.core.find(
        idVendor=id_vendor, idProduct=id_product, find_all=True)]

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

  def __iter__(self):
    while True:
      try:
        yield self.Read()
      except:
        return


class Stumpus(object):
  def __init__(self, device, bad=False, good=False, neutral=False):
    self._bad, self._good, self._neutral = bad, good, neutral
    self._device = device

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
      self._device.Write(ord(c))

class StumpusHandler(BaseHTTPServer.BaseHTTPRequestHandler):

  def do_GET(self):
    stumps = tuple(Stumpus(spark) for spark in Spark.All())
    request = self.path.partition('?')[0].split('/')
    self.send_header('Content-type','text/html')
    if len(request) != 3:
      self.send_response(404)
      self.end_headers()
      self.wfile.write('Example: http://stumpus/0/green')
      return
    _, indexes_str, statuses_str = request

    for i in indexes_str.split(','):
      try:
        stump = stumps[int(i)]
      except IndexError:
        self.send_response(404)
        self.end_headers()
        self.wfile.write('Spark not found.')
        return
      except ValueError:
        self.send_response(400)
        self.end_headers()
        self.wfile.write('Example: http://stumpus/0/green')
        return
      for status in statuses_str.split(','):
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
          self.wfile.write('Bad status string `%s`.' % status)
          return

    self.send_response(200)
    self.end_headers()
    self.wfile.write('Updated spark status.')


def main():
  httpd = BaseHTTPServer.HTTPServer(('', 8000), StumpusHandler)
  try:
    httpd.serve_forever()
  except KeyboardInterrupt:
    pass
  httpd.server_close()

if __name__ == '__main__':
  main()

