from __future__ import absolute_import, division, unicode_literals

import random
from collections import deque
from datetime import timedelta

from .timer import Timer

class StatsClientBase(object):
    """A Base class for various statsd clients."""

    def __init__(self):
        self._context = None

    def close(self):
        """Used to close and clean up any underlying resources."""
        raise NotImplementedError()
    
    def bind(self, tags):
        """
        Sets the context of the client. This binds the tags
        to the client so they're present when metrics are
        written out. Useful in reducing repeating tags in every
        function call
        """
        self._context = tags 

    def _build_stat_name(self, name, tags):
        """
        Builds a stat name in the format Graphite expects. Tags are appended
        in the series name

        ```
        my.series.name;tag1=value1;tag2=value2
        ```
        
        If tags have been binded to the client through a call to `bind`, they
        will be included in the stat name
        """
        if tags is None and self._context is None:
            return name
        
        if tags is None and self._context is not None:
            tags = self._context
        elif tags is not None and self._context is None:
            tags = tags
        else:
            tags.update(self._context)

        tags = ";".join(f"{k}={v}" for k, v in tags.items())
        stat_name = f"{name};{tags}"
        return stat_name

    def _send(self):
        raise NotImplementedError()

    def pipeline(self):
        raise NotImplementedError()

    def timer(self, stat, rate=1, tags=None):
        return Timer(self, stat, tags, rate)

    def timing(self, stat, delta, rate=1, tags=None):
        """
        Send new timing information.

        `delta` can be either a number of milliseconds or a timedelta.
        """
        if isinstance(delta, timedelta):
            # Convert timedelta to number of milliseconds.
            delta = delta.total_seconds() * 1000.
        self._send_stat(stat, tags, '%0.6f|ms' % delta, rate)

    def incr(self, stat, count=1, rate=1, tags=None):
        """Increment a stat by `count`."""
        self._send_stat(stat, tags, '%s|c' % count, rate)

    def decr(self, stat, count=1, rate=1, tags=None):
        """Decrement a stat by `count`."""
        self.incr(stat, -count, rate, tags)

    def gauge(self, stat, value, rate=1, delta=False, tags=None):
        """Set a gauge value."""

        if value < 0 and not delta:
            if rate < 1:
                if random.random() > rate:
                    return
            with self.pipeline() as pipe:
                pipe._send_stat(stat, tags, '0|g', 1)
                pipe._send_stat(stat, tags, '%s|g' % value, 1)
        else:
            prefix = '+' if delta and value >= 0 else ''
            self._send_stat(stat, tags, '%s%s|g' % (prefix, value), rate)

    def set(self, stat, value, rate=1, tags=None):
        """Set a set value."""
        self._send_stat(stat, tags, '%s|s' % value, rate)

    def _send_stat(self, stat, tags, value, rate):
        self._after(self._prepare(stat, tags, value, rate))

    def _prepare(self, stat, tags, value, rate):
        stat = self._build_stat_name(stat, tags)

        if rate < 1:
            if random.random() > rate:
                return
            value = '%s|@%s' % (value, rate)

        if self._prefix:
            stat = '%s.%s' % (self._prefix, stat)

        return '%s:%s' % (stat, value)

    def _after(self, data):
        if data:
            self._send(data)


class PipelineBase(StatsClientBase):

    def __init__(self, client):
        self._client = client
        self._prefix = client._prefix
        self._context = None
        self._stats = deque()

    def _send(self):
        raise NotImplementedError()

    def _after(self, data):
        if data is not None:
            self._stats.append(data)

    def __enter__(self):
        return self

    def __exit__(self, typ, value, tb):
        self.send()

    def send(self):
        if not self._stats:
            return
        self._send()

    def pipeline(self):
        return self.__class__(self)
