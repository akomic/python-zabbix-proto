Zabbix Proxy Sender
===================

|PyPI| |PyPI Count| |Build Status| |Coverage Status|

Disclaimer
==========

Quick Start
-----------

Connection settings

.. code:: python

    from ZabbixProxySender import ZabbixProxySender, ZabbixProxyPacket
    server = ZabbixProxySender('127.0.0.1', 10051)

Create a package and add the metric values. In the first example with
the current time, the second specified in unixtime format.

.. code:: python

    packet = ZabbixPacket('proxy name')
    packet.add('myhost','key', 'value')
    packet.add('myhost2', 'other_key', 'value2', 1455607162)

Now we send our package in Zabbix Server

.. code:: python

    server.send(packet)

And see the delivery status

.. code:: python

    print(server.status)

::

    {'info': 'processed: 2; failed: 0; total: 4; seconds spent: 0.207659',
     'response': 'success'}

.. |PyPI| image:: https://img.shields.io/pypi/v/ZabbixProxySender.svg
   :target: https://pypi.python.org/pypi/ZabbixProxySender
.. |PyPI Count| image:: https://img.shields.io/pypi/dw/ZabbixProxySender.svg
   :target: https://pypi.python.org/pypi/ZabbixProxySender
.. |Build Status| image:: https://travis-ci.org/akomic/zproxysender.svg?branch=master
   :target: https://travis-ci.org/akomic/zproxysender
.. |Coverage Status| image:: https://coveralls.io/repos/github/akomic/zproxysender/badge.svg?branch=master
   :target: https://coveralls.io/github/akomic/zproxysender?branch=master
