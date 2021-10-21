======================
A Python statsd client
======================

statsd_ is a friendly front-end to Graphite_. This is a Python client
for the statsd daemon.

Quickly, to use:

.. code-block:: python

    >>> import aerostatsd
    >>> c = aerostatsd.StatsClient('localhost', 8125)
    >>> c.incr('foo')  # Increment the 'foo' counter.
    >>> c.timing('stats.timed', 320)  # Record a 320ms 'stats.timed'.

You can also add a prefix to all your stats:

.. code-block:: python

    >>> import aerostatsd
    >>> c = aerostatsd.StatsClient('localhost', 8125, prefix='foo')
    >>> c.incr('bar')  # Will be 'foo.bar' in statsd/graphite.


Docs
====

There are lots of docs in the ``docs/`` directory and on ReadTheDocs_.


.. _statsd: https://github.com/etsy/statsd
.. _Graphite: https://graphite.readthedocs.io/
.. _ReadTheDocs: https://statsd.readthedocs.io/en/latest/index.html
