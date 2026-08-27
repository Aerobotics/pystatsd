from __future__ import absolute_import, division, unicode_literals

import socket
import time

from .base import StatsClientBase, PipelineBase


class Pipeline(PipelineBase):

    def __init__(self, client):
        super(Pipeline, self).__init__(client)
        self._maxudpsize = client._maxudpsize

    def _send(self):
        data = self._stats.popleft()
        while self._stats:
            # Use popleft to preserve the order of the stats.
            stat = self._stats.popleft()
            if len(stat) + len(data) + 1 >= self._maxudpsize:
                self._client._after(data)
                data = stat
            else:
                data += '\n' + stat
        self._client._after(data)


class StatsClient(StatsClientBase):
    """A client for aerostatsd."""

    def __init__(self, host='localhost', port=8125, prefix=None,
                 maxudpsize=512, ipv6=False, refresh_interval=60):
        """
        Create a new client.

        `refresh_interval` is the number of seconds between socket
        rebuilds, which give the client a new source port. Set to `None`
        to keep one socket for the lifetime of the client.
        """
        super(StatsClient, self).__init__()

        fam = socket.AF_INET6 if ipv6 else socket.AF_INET
        family, _, _, _, addr = socket.getaddrinfo(
            host, port, fam, socket.SOCK_DGRAM)[0]
        self._family = family
        self._addr = addr
        self._sock = socket.socket(family, socket.SOCK_DGRAM)
        self._prefix = prefix
        self._maxudpsize = maxudpsize
        self._refresh_interval = refresh_interval
        self._last_refresh = time.monotonic()

    def _refresh(self):
        """
        Rebuild the socket periodically, for a new source port.

        A load balancer that maps UDP flows to backends by source and
        destination address/port won't re-route a flow while traffic keeps
        flowing, so a flow pinned to a backend that has gone away silently
        black-holes. A new source port is a new flow, and gets routed
        afresh. The destination address is resolved once, in __init__.
        """
        if (self._refresh_interval is None
                or time.monotonic() - self._last_refresh
                < self._refresh_interval):
            return

        if self._sock is None:
            # Closed.
            return

        # Stamp before building, so a failure throttles retries.
        self._last_refresh = time.monotonic()

        try:
            sock = socket.socket(self._family, socket.SOCK_DGRAM)
        except socket.error:
            # Keep the current socket. Never raise over a metric.
            return

        old_sock = self._sock
        self._sock = sock
        old_sock.close()

    def _send(self, data):
        """Send data to statsd."""
        self._refresh()
        if self._sock is None:
            # Closed.
            return

        try:
            self._sock.sendto(data.encode('ascii'), self._addr)
        except (socket.error, RuntimeError):
            # No time for love, Dr. Jones!
            pass

    def close(self):
        if self._sock and hasattr(self._sock, 'close'):
            self._sock.close()
        self._sock = None

    def pipeline(self):
        return Pipeline(self)
