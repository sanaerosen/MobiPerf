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

"""Anonymized data visualization"""

__author__ = 'sanae@umich.edu (Sanae Rosen)' 

import logging

from django.utils import simplejson as json
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db

template_args = {"data":[{"traceroute": {"all": {"num_hops": 0, "ct": 1}, "ll.static.abc.com ": {"num_hops": 0, "ct": 1}}, "car": "t-mobile", "wk": 1, "lat": 48.1, "clu": 343, "net": "hspa+", "lng": -122.1, "ct": 0}, {"http": {"default": {"ct": 14, "avg_throughput": 145.27187242437293, "time": 709.5714285714286}, "all": {"ct": 14, "avg_throughput": 145.27187242437293, "time": 709.5714285714286}}, "car": "at&t", "traceroute": {"iad23s08-in-f17.1e100.net": {"avg_rtt": 155.97487214885956, "first_hop": 174.54764285714285, "num_hops": 15, "ct": 14}, "all": {"avg_rtt": 154.98258444317275, "first_hop": 143.91667901234575, "num_hops": 14, "ct": 162}, "www.google.com": {"avg_rtt": 140.6715533078033, "first_hop": 129.53333333333333, "num_hops": 12, "ct": 15}, "pb-in-f106.1e100.net": {"avg_rtt": 190.6211359002976, "first_hop": 135.177125, "num_hops": 15, "ct": 16}, "sea09s02-in-f17.1e100.net": {"avg_rtt": 172.38891904761905, "first_hop": 183.88107142857143, "num_hops": 15, "ct": 14}, "mlab1.sea01.measurement-lab.org": {"avg_rtt": 185.3526720238095, "first_hop": 139.12506249999998, "num_hops": 14, "ct": 16}, "ord08s07-in-f17.1e100.net": {"avg_rtt": 142.01242041047186, "first_hop": 137.69042857142855, "num_hops": 14, "ct": 14}, "den03s06-in-f19.1e100.net": {"avg_rtt": 149.02741292517004, "first_hop": 142.90478571428574, "num_hops": 14, "ct": 14}, "lga15s28-in-f16.1e100.net": {"avg_rtt": 146.4111245196324, "first_hop": 130.47614285714286, "num_hops": 16, "ct": 14}, "mia04s05-in-f18.1e100.net": {"avg_rtt": 137.66345555555557, "first_hop": 132.0222, "num_hops": 13, "ct": 15}, "mlab1.ord01.measurement-lab.org": {"avg_rtt": 155.05336222222223, "first_hop": 142.9334, "num_hops": 13, "ct": 15}, "www.youtube.com": {"avg_rtt": 124.62437999999999, "first_hop": 139.02213333333333, "num_hops": 11, "ct": 15}}, "wk": 1, "dns": {"all": {"ct": 29, "time": 937.1034482758621}, "mlab1.sea01.measurement-lab.org": {"ct": 15, "time": 1773.5333333333333}, "www.google.com": {"ct": 14, "time": 40.92857142857143}}, "lat": 35.9, "clu": 29, "net": "mobile", "ping": {"mlab1.hnd01.measurement-lab.org": {"packetloss": 0.006493506493506496, "max": 442.7857142857143, "ct": 14, "stdev": 67.0862619988535, "mean": 311.10714285714283}, "all": {"packetloss": 0.0021645021645021654, "max": 318.54761904761904, "ct": 42, "stdev": 51.48796790118573, "mean": 241.84000000000006}, "mlab1.lhr01.measurement-lab.org": {"packetloss": 0.0, "max": 328.85714285714283, "ct": 14, "stdev": 49.69898330995483, "mean": 265.1}, "www.google.com": {"packetloss": 0.0, "max": 184.0, "ct": 14, "stdev": 37.678658394748894, "mean": 149.31285714285715}}, "lng": -78.9, "ct": 0}, {"traceroute": {"iad23s08-in-f17.1e100.net": {"avg_rtt": 712.04, "first_hop": 154.667, "num_hops": 25, "ct": 1}, "all": {"avg_rtt": 552.271125414763, "first_hop": 262.12499999999994, "num_hops": 21, "ct": 8}, "www.google.com": {"avg_rtt": 624.9374375000001, "first_hop": 964.333, "num_hops": 16, "ct": 1}, "sea09s02-in-f17.1e100.net": {"avg_rtt": 697.4920952380953, "first_hop": 192.0, "num_hops": 21, "ct": 1}, "mlab1.sea01.measurement-lab.org": {"avg_rtt": 379.7157647058824, "first_hop": 283.667, "num_hops": 17, "ct": 1}, "den03s06-in-f19.1e100.net": {"avg_rtt": 440.3864090909091, "first_hop": 69.333, "num_hops": 22, "ct": 2}, "lga15s28-in-f16.1e100.net": {"avg_rtt": 696.7308076923075, "first_hop": 186.0, "num_hops": 26, "ct": 1}, "mlab1.ord01.measurement-lab.org": {"avg_rtt": 426.48008000000004, "first_hop": 177.667, "num_hops": 25, "ct": 1}}, "car": "yes optus", "wk": 1, "http": {"default": {"ct": 2, "avg_throughput": 4.576941344098789, "time": 8422.0}, "all": {"ct": 2, "avg_throughput": 4.576941344098789, "time": 8422.0}}, "dns": {"mlab1.sea01.measurement-lab.org": {"ct": 2, "time": 648.0}, "all": {"ct": 3, "time": 434.6666666666667}, "www.google.com": {"ct": 1, "time": 8.0}}, "lat": -33.7, "clu": 94, "net": "mobile", "ping": {"all": {"packetloss": 0.0, "max": 396.5, "ct": 2, "stdev": 81.509747090251, "mean": 156.515}, "www.google.com": {"packetloss": 0.0, "max": 396.5, "ct": 2, "stdev": 81.509747090251, "mean": 156.515}}, "lng": 150.6, "ct": 0}, {"car": "at&t", "wk": 1, "lat": 29.9, "clu": 148, "net": "mobile", "lng": -90.1, "ct": 0}, {"car": "network norway", "wk": 1, "lat": 33.8, "clu": 0, "net": "mobile: ", "lng": -84.3, "ct": 0}]}
class Visualize(webapp.RequestHandler):
    def Visualize(self, **unused_args):
        self.response.out.write(template.render(
            'templates/visualization.html', template_args))






