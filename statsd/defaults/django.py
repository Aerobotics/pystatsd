from __future__ import absolute_import
import os
from django.conf import settings

from statsd import defaults
from statsd.client import StatsClient


STATSD_PREFIX = "aerobotics.service"

statsd = None

if statsd is None:
    host = os.getenv("STATSD_HOST", defaults.HOST)
    port = getattr(settings, 'STATSD_PORT', defaults.PORT)
    prefix = STATSD_PREFIX
    maxudpsize = getattr(settings, 'STATSD_MAXUDPSIZE', defaults.MAXUDPSIZE)
    ipv6 = False
    statsd = StatsClient(host=host, port=port, prefix=prefix,
                         maxudpsize=maxudpsize, ipv6=ipv6)
