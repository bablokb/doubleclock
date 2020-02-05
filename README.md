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
  - one 5-way button for setup
  - one normal button for start/stop
  - one slider
  - one active buzzer

![](doc/doubleclock-breadboard.png)

You can find details on the necessary wiring in `doc/specs.md`.


Software
--------

Run

    git clone https://github.com/bablokb/doubleclock.git
    cd doubleclock
    sudo tools/install

to install the software and some prerequisite packages. This will also enable
a systemd-service so that the clock starts at boot-time.


Usage
-----

Push the 5-way button down to enable or disable setup-mode. In setup-mode the
active digit of the active clock will blink. Use the slider to switch between
clocks. Pushing the button to the left or right will change the active digit,
pushing it up or down will change the value. After setting the alarm-times,
push the button down again to leave setup-mode. Note that pressing the
start/stop-button in setup-mode will reset all values to zero.

Use the start/stop-button to activate the countdown. As soon as a clock
reaches zero, the buzzer will start and the brightness of the display is
reduced. Note that after the alarm starts, the display will continue to
count.

In alarm-mode, the start/stop-button will stop the buzzer, but not the second
running clock. Stopping the second alarm will reset the values to the state
after the last setup.

License
-------

The code in `files/usr/local/sbin/doubleclock.py` is licensed under the GPLv3.

The library in `files/usr/local/sbin/TM1637.py` is from
[https://github.com/bablokb/circuitpython-tm1637](https://github.com/bablokb/circuitpython-tm1637)
and is distributed under a MIT-license.
