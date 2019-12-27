Kitchen-Clock with two countdown-timers (based on TM1637-displays)
==================================================================

Overview
--------

This project implements a double countdown clock (kitchen-timer) using
two TM1637 displays (and some additional components, see below).

The "firmware" uses Python3 and is expected to run on a Raspberry Pi Zero
(or a similar SBC). Porting to a MCU should be an easy task if you have
enough experience.


Hardware
--------

The setup uses the following hardware-components:

  - two TM1637 clock displays
  - one 5-way button
  - one normal button
  - one slider

You can find details on the necessary wiring in `doc/specs.md`.


Software
--------

Run

    git clone https://github.com/bablokb/doubleclock.git
    cd doubleclock
    sudo tools/install

to install the software and some prerequisite packages. This will also enable
a systemd-service so that the clock starts at boot-time.


License
-------

The code in `files/usr/local/sbin/doubleclock.py` is licensed under the GPLv3.

The library in `files/usr/local/sbin/TM1637.py` is from
[https://github.com/bablokb/circuitpython-tm1637](https://github.com/bablokb/circuitpython-tm1637)
and is distributed under a MIT-license.
