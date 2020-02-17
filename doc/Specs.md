Technical Specifications
========================

Operation
---------

The *slider* changes between the two clocks. The 5-way button changes the
clock values. The *start/stop* button starts and stops the countdown and
turns of the buzzer. A long press of *start/stop* resets both clocks.

Up to four memory buttons save/recall the current values. Pressing a
memory button while in setup-state will save the values. Pressing the button
in ready-state will recall the values.

The clocks display a countdown in the format "MM:SS" with MM ranging from
0-99 and seconds from 0-59.


States
------

Possible states:

  - *init*: both clocks show "00:00"
  - *setup*: one digit of the active clock is blinking
  - *ready*: one or both clocks are ready to run
  - *running*: one or both clocks are running
  - *alarm*: the buzzer is ringing


Transitions
-----------

  - *init*    + *set/push*   -> *setup*
  - *setup*   + *set/push*   -> *ready*
  - *setup*   + *left/right* -> *setup* (change digit)
  - *setup*   + *up/down*    -> *setup* (increase/decrease value of digit)
  - *setup*   + *start*      -> *init*
  - *ready*   + *start/stop* -> *running*
  - *running* + *start/stop* -> *ready*
  - *alarm*   + *start/stop* -> *running* (stop buzzer) or *ready*


Pin Configuration
-----------------

This is just for information and might not be up-to-date. The truth is
in the code (file `doubleclock.py`).


| Function          | Pi-Zero |
|-------------------|---------|
| set (push)        | 17      |
| up                | 18      |
| down              | 22      |
| left              | 27      |
| right             | 23      |
| slider (left)     | 20      |
| start/stop        | 05      |
| clock (left,clk)  | 06      |
| clock (left,dio)  | 13      |
| clock (right,clk) | 12      |
| clock (right,dio) | 16      |
| buzzer            | 26      |
| mem1              | 09      |
| mem2              | 25      |
| mem3              | 11      |
| mem4              | 08      |
