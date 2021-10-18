from __future__ import absolute_import
import os
import warnings

from statsd import defaults
from statsd.client import StatsClient

STATSD_PREFIX = "aerobotics.application"

statsd = None

if statsd is None:
    host = os.getenv("STATSD_HOST", defaults.HOST)
    port = int(os.getenv("STATSD_PORT", defaults.PORT))
    prefix = STATSD_PREFIX
    maxudpsize = int(os.getenv("STATSD_MAXUDPSIZE", defaults.MAXUDPSIZE))
    ipv6 = False
    statsd = StatsClient(host=host, port=port, prefix=prefix, maxudpsize=maxudpsize, ipv6=ipv6)

    environment = os.getenv("ENVIRONMENT_NAME", "dev")
    application = os.getenv("APPLICATION_NAME")

    tags = {"environment": environment}

    if application is not None:
        tags["application"] = application
    else:
        warnings.warn(
            "Application name not set. Could not find environment "
            "variable APPLICATION_NAME. This will make it difficult "
            "to query for these metrics."
        )

    statsd.bind(tags={"environment": environment})
