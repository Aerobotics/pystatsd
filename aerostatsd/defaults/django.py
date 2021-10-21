from __future__ import absolute_import
import os

from aerostatsd import defaults
from aerostatsd.client import StatsClient


STATSD_PREFIX = "aerobotics.service"

statsd = None

if statsd is None:
    host = os.getenv("STATSD_HOST", defaults.HOST)
    port = os.getenv('STATSD_PORT', defaults.PORT)
    prefix = STATSD_PREFIX
    maxudpsize = os.getenv('STATSD_MAXUDPSIZE', defaults.MAXUDPSIZE)
    ipv6 = False
    statsd = StatsClient(host=host, port=port, prefix=prefix,
                         maxudpsize=maxudpsize, ipv6=ipv6)
