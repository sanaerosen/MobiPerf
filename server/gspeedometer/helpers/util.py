# Copyright 2012 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#!/usr/bin/python2.4
#

"""Utility functions for the Mobiperf service."""

__author__ = 'mdw@google.com (Matt Welsh)'

import base64
import datetime
from django.utils import simplejson as json
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from gspeedometer import config_private
# due to name collisions
import hashlib
import logging
import time


def StringToTime(thestr):
  """Convert an ISO8601 timestring into a datetime object."""
  try:
    strtime, extra = thestr.split('.')
  except:
    # Must not be a '.' in the string
    strtime = thestr[:-1]  # Get rid of 'Z' at end
    extra = 'Z'
  dt = datetime.datetime(*time.strptime(strtime, "%Y-%m-%dT%H:%M:%S")[0:6])
  # Strip 'Z' off of end
  if (extra[-1] != 'Z'): raise ValueError, "Timestring does not end in Z"
  usecstr = extra[:-1]
  # Append extra zeros to end of usecstr if needed
  while (len(usecstr) < 6):
    usecstr = usecstr + '0'
  usec = int(usecstr)
  dt = dt.replace(microsecond=usec)
  return dt


def TimeToString(dt):
  """Convert a DateTime object to an ISO8601-encoded string."""
  return dt.isoformat() + 'Z'


def MicrosecondsSinceEpochToTime(microsec_since_epoch):
  """Convert microseconds since epoch UTC to a datetime object."""
  sec = int(microsec_since_epoch / 1000000)
  usec = int(microsec_since_epoch % 1000000)
  dt = datetime.datetime.utcfromtimestamp(sec)
  dt = dt.replace(microsecond=usec)
  return dt


def TimeToMicrosecondsSinceEpoch(dt):
  """Convert a datetime object to microseconds since the epoch UTC."""
  epoch = datetime.datetime(1970, 1, 1)
  diff = dt - epoch
  microsec_since_epoch = int(((diff.days * 86400) + (diff.seconds)) * 1000000)
  microsec_since_epoch += diff.microseconds
  return microsec_since_epoch


_SIMPLE_TYPES = (int, long, float, bool, dict, basestring, list)


def ConvertToDict(model, include_fields=None, exclude_fields=None,
                  timestamps_in_microseconds=False, location_precision=None):
  """Convert an AppEngine Model object to a Python dict ready for json dump.

     For each property in the model, set a value in the returned dict
     with the property name as its key.
     
     location_precision: if not None, it specifies how location precision. The 
     code will multiply by this value, take the integer value and divide by 
     this value. In other words, we're giving precision to the 
     'location_precision'ths. If it's ten, we're giving tenths of a degree.
  """
  output = {}
  for key, prop in model.properties().iteritems():
    if include_fields is not None and key not in include_fields: continue
    if exclude_fields is not None and key in exclude_fields: continue
    value = getattr(model, key)
    if value is None or isinstance(value, _SIMPLE_TYPES):
      output[key] = value
    elif isinstance(value, datetime.date):
      if timestamps_in_microseconds:
        output[key] = TimeToMicrosecondsSinceEpoch(value)
      else:
        output[key] = TimeToString(value)
    elif isinstance(value, db.GeoPt):
      if not location_precision:
        output[key] = {'latitude': value.lat, 'longitude': value.lon}
      else:
        lat = int(value.lat * location_precision) / float(location_precision)
        lon = int(value.lon * location_precision) / float(location_precision)
        output[key] = {'latitude': lat, 'longitude': lon}
    elif isinstance(value, db.Model):
      output[key] = ConvertToDict(value, include_fields, exclude_fields,
                                  timestamps_in_microseconds,
                                  location_precision)
    elif isinstance(value, users.User):
      # we do not need nor want to store user info in the archive
      pass
    else:
      raise ValueError('cannot encode ' + repr(prop))
  return output


def ConvertToJson(model, include_fields=None, exclude_fields=None):
  """Convert an AppEngine Model object to a JSON-encoded string."""
  return json.dumps(ConvertToDict(model, include_fields, exclude_fields))


def ConvertFromDict(model, input_dict, include_fields=None,
                    exclude_fields=None):
  """Fill in Model fields with values from a dict.

     For each key in the dict, set the value of the corresponding field
     in the given Model object to that value.

     If the Model implements a method 'JSON_DECODE_key' for a given key 'key',
     this method will be invoked instead with an argument containing
     the value. This allows Model subclasses to override the decoding
     behavior on a per-key basis.
  """
  for k, v in input_dict.items():
    if include_fields is not None and k not in include_fields: continue
    if exclude_fields is not None and k in exclude_fields: continue
    if hasattr(model, 'JSON_DECODE_' + k):
      method = getattr(model, 'JSON_DECODE_' + k)
      method(v)
    else:
      setattr(model, k, v)

class PstTzinfo(datetime.tzinfo):
  def utcoffset(self, dt): return datetime.timedelta(hours= -7)
  def dst(self, dt): return datetime.timedelta(0)
  def tzname(self, dt): return 'PST+07PDT'
  def olsen_name(self): return 'US/Pacific'

class UtcTzinfo(datetime.tzinfo):
  def utcoffset(self, dt): return datetime.timedelta(hours=0)
  def dst(self, dt): return datetime.timedelta(0)
  def tzname(self, dt): return 'UTC'
  def olsen_name(self): return 'UTC'

TZINFOS = {
  'pst': PstTzinfo(),
  'utc': UtcTzinfo()
}

def translate(self, timestamp):
    """Translates a UTC datetime to the env_tz query parameter's time zone.

    Args:
      timestamp: A datetime instance.

    Returns:
      A (str, datetime) tuple. The string is the code snippet used to
      translate the timestamp, and the datetime is the result.
    """
    translate_to = self.request.get('translate_to', 'nothing')
    translate_with = self.request.get('translate_with', 'astimezone()')
    utc = TZINFOS['utc']

    if translate_to == 'nothing':
      return ('no translation', 'N/A')
    elif translate_with == 'astimezone':
      timestamp = timestamp.replace(tzinfo=utc)
      return ('timestamp.astimezone(to_tzinfo)',
              timestamp.astimezone(TZINFOS[translate_to]))
    else:
      return ('invalid translation', 'invalid translation')

def _getDeviceProperties(device_info, time, device_properties_database):
  """Return the DeviceProperties entry closest to an RRC state measurement.
  
  Args:
    device_info: The corresponding device info instance. Access control
      should have been resolved when fetching this.
    time: A datetime instance when the RRC measurements were taken.
    device_properties_database: Pass the device properties database to avoid
      import problems.
      
  Returns:
    The corresponding DeviceProperties entry closest in time to the RRC 
    measurements."""

  query = device_properties_database.all()
  query.filter("device_info=", device_info)
  query.filter("timestamp < ", time)
  query.order("-timestamp")
  candidate_1 = query.fetch(1)

  query = device_properties_database.all()
  query.filter("device_info=", device_info)
  query.filter("timestamp > ", time)
  query.order("timestamp")
  candidate_1 = query.fetch(1)
  
  if (candidate_1.timestamp - time) > (time - candidate_2.timestamp):
    return candidate_2
  return candidate_1

def RRCMeasurementListToDictList(measurement_list, device_info_database, \
     include_fields = None, exclude_fields=None, location_precision=None):
  """Converts a list of rrc measurement entities into a list of dictionaries.

  Given a list of measuerment model objects from the datastore, this method
  will convert that list into a list of python dictionaries that can then
  be serialized.

  Args:
    measurement_list: A list of measurement entities from the datastore.
    device info instance. Is not actually put in the data structure returned.
    device_info_database: Pass the database of device info here.
        We need to do it this way to avoid import problems.
    include_fields: A list of attributes for the entities that should be
        included in the serialized form.
    exclude_fields: A list of attributes for the entities that should be
        excluded in the serialized form.
    location_precision: Precision for location measurements. If you want 
        n significant figures, specify 10^n for this value.
  
  Returns:
    A list of dictionaries representing the list of measurement entities.

  Raises:
    db.ReferencePropertyResolveError: handled for the cases where a device has
        been deleted and where task has been deleted.
    No New exceptions generated here.
  """
  output = list()

  # First, fetch the corresponding device info
  
  device_info_dict = {}

  for item in  device_info_database.GetDeviceListWithAcl():
      device_info_dict[item.id] = item

  for measurement in measurement_list:
    device_id = measurement.phone_id

    mdict = ConvertToDict(measurement, include_fields, exclude_fields, \
      True, None)

    # Fill in additional fields

    # We want to preserve test id/phone id pairs without being able to tie 
    # measurements together when anonymizing. 
    mdict["test_id"] = HashDeviceId(str(measurement.test_id) +
        measurement.phone_id)
    
    # Find the device info corresponding and save it
    if device_id in device_info_dict:
      device_info = device_info_dict[device_id]     
      mdict["device_info"] = ConvertToDict(device_info, include_fields, \
          exclude_fields, True, None)

    # Fing the device properties coresponding to the device info and closest in time
    output.append(mdict)

  return output



def MeasurementListToDictList(measurement_list, include_fields=None,
    exclude_fields=None, location_precision=None):
  """Converts a list of measurement entities into a list of dictionaries.

  Given a list of measuerment model objects from the datastore, this method
  will convert that list into a list of python dictionaries that can then
  be serialized.

  Args:
    measurement_list: A list of measurement entities from the datastore.
    include_fields: A list of attributes for the entities that should be
        included in the serialized form.
    exclude_fields: A list of attributes for the entities that should be
        excluded in the serialized form.
    location_precision: Precision for location measurements. If you want 
        n significant figures, specify 10^n for this value.
  
  Returns:
    A list of dictionaries representing the list of measurement entities.

  Raises:
    db.ReferencePropertyResolveError: handled for the cases where a device has
        been deleted and where task has been deleted.
    No New exceptions generated here.
  """
  #TODO(gavaletz) make this iterate over a query instead of a list.
  output = list()
  for measurement in measurement_list:
    # Need to catch case where device has been deleted
    try:
      unused_device_info = measurement.device_properties.device_info
    except db.ReferencePropertyResolveError:
      logging.exception('Device deleted for measurement %s',
          measurement.key().id())
      # Skip this measurement
      continue

    # Need to catch case where task has been deleted
    try:
      unused_task = measurement.task
    except db.ReferencePropertyResolveError:
      measurement.task = None
      measurement.put()

    mdict = ConvertToDict(measurement, include_fields, exclude_fields,
        True, location_precision)

    # Fill in additional fields
    mdict['id'] = str(measurement.key().id())
    mdict['parameters'] = measurement.Params()
    mdict['values'] = measurement.Values()

    if 'task' in mdict and mdict['task'] is not None:
      mdict['task']['id'] = str(measurement.GetTaskID())
      mdict['task']['parameters'] = measurement.task.Params()

    output.append(mdict)
  return output

def GetTypeAllocationCode(imei):
  """Returns the 'type allocation code' (TAC) from the IMEI."""
  return imei[0:8]

def HashDeviceId(imei):
  """Returns a salted hash of the unique portion of IMEI."""
  # Unique portion of IMEI starts at index 8.
  rest = imei[8:]
  # Add salt, get hash.
  salted = config_private.IMEI_SALT[0:16] + rest + config_private.IMEI_SALT[16:]
  m = hashlib.md5()
  m.update(salted)
  # Base64 encoding to save space.
  return base64.b64encode(m.digest(), '._').strip('=')
