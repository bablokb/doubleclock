#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Countdown-clock with two clocks
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/doubleclock
#
# ----------------------------------------------------------------------------

import threading, signal, sys, time, pickle
import TM1637
import board
import RPi.GPIO as GPIO

# --- file for persistent configuration   ------------------------------------

CONF_FILE = "/root/doubleclock.data"

# --- pin-configuration   ----------------------------------------------------

PIN_PUSH      = 17
PIN_UP        = 18
PIN_DOWN      = 22
PIN_LEFT      = 27
PIN_RIGHT     = 23
PIN_SLIDER_L  = 20
PIN_START     =  5
PIN_LCLOCK_C  = board.D6
PIN_LCLOCK_D  = board.D13
PIN_RCLOCK_C  = board.D12
PIN_RCLOCK_D  = board.D16
PIN_BUZZER    = 26
PIN_BUZZER_ON = GPIO.LOW                   # change to GPIO.HIGH if necessary

# --- application-class   ----------------------------------------------------

class DoubleClock(object):

  _STATE_INIT    = 0
  _STATE_SETUP   = 1
  _STATE_READY   = 2
  _STATE_RUNNING = 3
  _STATE_ALARM   = 4
  _BUZZ_WARN     = (0.25,1)                # (duration,repeat)
  _BUZZ_ALARM    = [(0.25,20),(0.5,-1)]    # second alarm runs indefinitely
  _BRIGHTNESS    = 7                       # maximum brightness
  
  # --- constructor   --------------------------------------------------------

  def __init__(self):
    """ constructor """

    self._exit_ev  = threading.Event()         # exit event
    self._count_ev = threading.Event()         # countdown
    self._buzz_ev  = threading.Event()         # buzzer
    self._buzz_thread  = None
    self._clocks   = [                         # left-clock: index is 0
        TM1637.TM1637(PIN_LCLOCK_C,PIN_LCLOCK_D),
        TM1637.TM1637(PIN_RCLOCK_C,PIN_RCLOCK_D)
      ]

    GPIO.setmode(GPIO.BCM)

    GPIO.setup(PIN_PUSH,     GPIO.IN)
    GPIO.setup(PIN_UP,       GPIO.IN)
    GPIO.setup(PIN_DOWN,     GPIO.IN)
    GPIO.setup(PIN_LEFT,     GPIO.IN)
    GPIO.setup(PIN_RIGHT,    GPIO.IN)
    GPIO.setup(PIN_SLIDER_L, GPIO.IN,  pull_up_down=GPIO.PUD_UP)
    GPIO.setup(PIN_START,    GPIO.IN,  pull_up_down=GPIO.PUD_UP)
    GPIO.setup(PIN_BUZZER,   GPIO.OUT, initial=1-PIN_BUZZER_ON)

    GPIO.add_event_detect(PIN_PUSH,     GPIO.FALLING,      self.on_push)
    GPIO.add_event_detect(PIN_UP,       GPIO.FALLING,        self.on_up)
    GPIO.add_event_detect(PIN_DOWN,     GPIO.FALLING,      self.on_down)
    GPIO.add_event_detect(PIN_LEFT,     GPIO.FALLING,      self.on_left)
    GPIO.add_event_detect(PIN_RIGHT,    GPIO.FALLING,     self.on_right)
    GPIO.add_event_detect(PIN_SLIDER_L, GPIO.BOTH,       self.on_slider)
    GPIO.add_event_detect(PIN_START,    GPIO.FALLING, self.on_start,200)

    self._reset()
    self._restore()

  # --- reset internal state   -----------------------------------------------

  def _reset(self):
    self._state    = DoubleClock._STATE_INIT   # global state
    self._values   = [[0,0,0,0], [0,0,0,0]]    # digit-values
    self._dig_nr   = [0,0]                     # current digit-number
    self._clock_nr = GPIO.input(PIN_SLIDER_L)  # current "active" clock
    
  # --- restore clock-values from persistent storage   -----------------------

  def _restore(self):
    try:
      with open(CONF_FILE,"rb") as f:
        self._values = pickle.load(f)
    except:
      pass

  # --- save clock-values to persistent storage   ----------------------------

  def _save(self):
    """ save values - might fail if system is read-only """
    try:
      with open(CONF_FILE,"wb") as f:
        pickle.dump(self._values,f)
    except:
      pass

  # --- process set (push)   -------------------------------------------------

  def on_push(self,pin):
    if self._state == DoubleClock._STATE_INIT:
      self._state = DoubleClock._STATE_SETUP
    elif self._state == DoubleClock._STATE_SETUP:
      self._save()
      self._state = DoubleClock._STATE_READY
    elif self._state == DoubleClock._STATE_READY:
      self._state = DoubleClock._STATE_SETUP

  # --- process left   -------------------------------------------------------

  def on_left(self,pin):
    if not self._state == DoubleClock._STATE_SETUP:
      self.buzz(*DoubleClock._BUZZ_WARN)
    else:
      self._dig_nr[self._clock_nr] = (self._dig_nr[self._clock_nr] + 1) % 4

  # --- process right   ------------------------------------------------------

  def on_right(self,pin):
    if not self._state == DoubleClock._STATE_SETUP:
      self.buzz(*DoubleClock._BUZZ_WARN)
    else:
      self._dig_nr[self._clock_nr] = (self._dig_nr[self._clock_nr] + 3) % 4

  # --- process up   ---------------------------------------------------------

  def on_up(self,pin):
    if not self._state == DoubleClock._STATE_SETUP:
      self.buzz(*DoubleClock._BUZZ_WARN)
      return

    clock = self._clock_nr
    digit = self._dig_nr[clock]
    old   = self._values[clock][digit]
    if digit == 1:
      # 10-seconds
      self._values[clock][digit] = (old+1) % 6
    else:
      # 1-seconds, 1-minutes, 10-minutes
      self._values[clock][digit] = (old+1) % 10

  # --- process down   -------------------------------------------------------

  def on_down(self,pin):
    if not self._state == DoubleClock._STATE_SETUP:
      self.buzz(*DoubleClock._BUZZ_WARN)
      return

    clock = self._clock_nr
    digit = self._dig_nr[clock]
    old   = self._values[clock][digit]
    if digit == 1:
      # 10-seconds
      self._values[clock][digit] = (old+5) % 6
    else:
      # 1-seconds, 1-minutes, 10-minutes
      self._values[clock][digit] = (old+9) % 10

  # --- process start   ------------------------------------------------------

  def on_start(self,pin):
    if self._state == DoubleClock._STATE_INIT:
      # not supported, just buzz
      self.buzz(*DoubleClock._BUZZ_WARN)

    elif self._state == DoubleClock._STATE_SETUP:
      # reset digits during setup-mode
      self._reset()

    elif self._state == DoubleClock._STATE_READY:
      # start alarms

      # calculate seconds per clock ...
      self._secs = [0,0]
      for i in range(2):
        self._secs[i] = (10*60*self._values[i][3] + 60*self._values[i][2] +
                         10*self._values[i][1] +    self._values[i][0])
      
      if self._secs[0] + self._secs[1] > 0:
        self._count_ev.clear()
        self._state    = DoubleClock._STATE_RUNNING
        # ... and start alarm-thread
        threading.Thread(target=self._count).start()

    elif self._state == DoubleClock._STATE_RUNNING:
      # stop countdown and reset to ready-state
      self._count_ev.set()
      self._state = DoubleClock._STATE_READY

    elif self._state == DoubleClock._STATE_ALARM:
      # turn off buzzer
      self._buzz_ev.set()
      if self._secs[0] <= 0 and self._secs[1] <= 0:
        # both alarms are finished, so stop count-down
        self._state = DoubleClock._STATE_READY
        self._count_ev.set()
      else:
        # one alarm is still running
        self._state = DoubleClock._STATE_RUNNING

  # --- process exit   -------------------------------------------------------

  def on_exit(self):
    self._count_ev.set()
    self._buzz_ev.set()
    self._exit_ev.set()

  # --- process slider   -----------------------------------------------------

  def on_slider(self,pin):
    self._clock_nr = GPIO.input(PIN_SLIDER_L)

  # --- ring the buzzer   ----------------------------------------------------

  def buzz(self,duration,count=1):
    if self._buzz_thread:                # buzzer already buzzing
      return
    self._buzz_ev.clear()
    self._buzz_thread = threading.Thread(
      target=self._buzz,args=(duration,count))
    self._buzz_thread.start()

  # --- run the main thread   ------------------------------------------------

  def run(self):
    threading.Thread(target=dclock._update).start()

  # --- update the clock-chips   ---------------------------------------------

  def _update(self):
    """ we update every 0.5 secs to implement blinking """

    blink_off = False
    while True:
      t1 = time.monotonic()
      if self._state in [DoubleClock._STATE_ALARM,DoubleClock._STATE_RUNNING]:
        # update using self._secs
        for i in [0,1]:
          (m,s) = divmod(abs(self._secs[i]),60)
          self._clocks[i].numbers(m,s)
          if not self._secs[i]:
            # timer reached zero, so dim display
            self._clocks[i].brightness(0)
      else:
        # update using self._values
        for i in [0,1]:
          self._clocks[i].brightness(DoubleClock._BRIGHTNESS)
          # copy array of int to array of strings
          val = [str(self._values[i][j]) for j in range(3,-1,-1)]
          if (self._state == DoubleClock._STATE_SETUP and blink_off and
                                                          self._clock_nr == i):
            # the current digit of active clock will blink
            val[3-self._dig_nr[i]] = " "
          digits = "%s%s%s%s" % (*val,)
          self._clocks[i].show(digits,True)
        blink_off = not blink_off

      # wait up to 0.5 seconds (take time lost in logic into account)
      delay = max(0.0,0.5-(time.monotonic()-t1))
      if self._exit_ev.wait(delay):
        break

    # cleanup (clear displays)
    for i in [0,1]:
      self._clocks[i].show(" "*4,False)

  # --- ring the buzzer   ----------------------------------------------------

  def _buzz(self,duration,count):
    """ passing count=-1 will sound the buffer indefintely """

    while count != 0:
      GPIO.output(PIN_BUZZER,PIN_BUZZER_ON)   # buzzer on
      if self._buzz_ev.wait(duration):        # wait and check for interrupt
        break
      GPIO.output(PIN_BUZZER,1-PIN_BUZZER_ON) # buzzer off
      if self._buzz_ev.wait(duration):        # wait and check for interrupt
        break
      count -= 1
    GPIO.output(PIN_BUZZER,1-PIN_BUZZER_ON)   # buzzer off
    self._buzz_thread = None

  # --- count down the remaining seconds   -----------------------------------

  def _count(self):
    """ count down both clocks, exit on external event """

    # we don't want to count-down a clock which is already 0 at start
    use_clock = [self._secs[0] > 0, self._secs[1] > 0]

    # count-down the seconds and sleep inbetween
    while True:
      t1 = time.monotonic()
      if self._state in [DoubleClock._STATE_ALARM,DoubleClock._STATE_RUNNING]:
        for i in [0,1]:
          if use_clock[i]:
            self._secs[i] -= 1
            if not self._secs[i]:
              # countdown reached zero, so stop old and start new alarm
              if self._buzz_thread:
                self._buzz_ev.set()
                try:
                  self._buzz_thread.join()
                except:
                  pass
              self._state = DoubleClock._STATE_ALARM
              self.buzz(*DoubleClock._BUZZ_ALARM[i])

      # wait up to one second (take time lost in logic into account)
      delay = max(0.0,1-(time.monotonic()-t1))

      if self._count_ev.wait(delay):
        return

# --------------------------------------------------------------------------

def signal_handler(_signo, _stack_frame):
  """ Signal-handler to cleanup threads """

  global dclock
  dclock.on_exit()
  sys.exit(0)

# --------------------------------------------------------------------------

if __name__ == "__main__":

  # create objects and run update thread
  dclock = DoubleClock()
  dclock.run()

  # setup signal handlers
  signal.signal(signal.SIGTERM, signal_handler)
  signal.signal(signal.SIGINT, signal_handler)

  # --- main loop   ---------------------------------------------------------

  signal.pause()
