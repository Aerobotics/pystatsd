from __future__ import absolute_import, division, unicode_literals

import socket
import threading
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

        `refresh_interval` is the number of seconds to cache the resolved
        address before re-resolving it, so DNS changes (e.g. the statsd
        host moving to a new IP) are eventually picked up. Set to `None`
        to resolve once and never refresh.
        """
        super(StatsClient, self).__init__()

        self._host = host
        self._port = port
        self._fam = socket.AF_INET6 if ipv6 else socket.AF_INET
        self._refresh_interval = refresh_interval
        self._prefix = prefix
        self._maxudpsize = maxudpsize
        self._lock = threading.Lock()

        self._connect()

    def _connect(self):
        # Record the attempt before resolving, so a failed or slow
        # resolution still throttles retries to refresh_interval instead
        # of being retried on every subsequent send.
        self._last_connect = time.monotonic()

        family, _, _, _, addr = socket.getaddrinfo(
            self._host, self._port, self._fam, socket.SOCK_DGRAM)[0]
        sock = socket.socket(family, socket.SOCK_DGRAM)

        old_sock = getattr(self, '_sock', None)
        self._addr = addr
        self._sock = sock

        if old_sock is not None:
            old_sock.close()

    def _refresh_connection(self):
        if (self._refresh_interval is None
                or time.monotonic() - self._last_connect
                < self._refresh_interval):
            return

        with self._lock:
            # Re-check now that we hold the lock, in case another
            # thread already refreshed while we were waiting for it.
            if (time.monotonic() - self._last_connect
                    >= self._refresh_interval):
                try:
                    self._connect()
                except socket.error:
                    # Keep using the old socket/address if
                    # re-resolution fails.
                    pass

    def _send(self, data):
        """Send data to statsd."""
        self._refresh_connection()

        # Snapshot both together so a concurrent _connect() can't hand us
        # a mismatched (old socket, new address) or (new socket, old
        # address) pair.
        with self._lock:
            sock = self._sock
            addr = self._addr

        if sock is None:
            # Closed concurrently.
            return

        try:
            sock.sendto(data.encode('ascii'), addr)
        except (socket.error, RuntimeError):
            # No time for love, Dr. Jones!
            pass

    def close(self):
        with self._lock:
            sock = self._sock
            self._sock = None

        if sock is not None and hasattr(sock, 'close'):
            sock.close()

    def pipeline(self):
        return Pipeline(self)
