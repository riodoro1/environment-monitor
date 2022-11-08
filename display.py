#!/home/rafal/environment-monitor/venv/bin/python

import sys
from hd44780 import hd44780
from measurer import MeasurementsArchive

from time import sleep

if __name__ == "__main__":
  if len(sys.argv) == 2:
    archive = MeasurementsArchive(sys.argv[1])
  else:
    raise RuntimeError("No archive path in argv")

  archive.open()
  lcd = hd44780(hd44780.default_pinmap)

  clock_character = [
    0b00000,
    0b01110,
    0b11011,
    0b10011,
    0b11111,
    0b01110,
    0b00000,
    0b00000
  ]
  lcd.add_character(clock_character, 0)

  degree_character = [
    0b00110,
    0b01001,
    0b01001,
    0b00110,
    0b00000,
    0b00000,
    0b00000,
    0b00000]
  lcd.add_character(degree_character, 1)

  thermometer_character = [
    0b00100,
    0b01010,
    0b01010,
    0b01110,
    0b11111,
    0b11111,
    0b01110,
    0b00000
  ]
  lcd.add_character(thermometer_character, 2)

  drop_character = [
    0b00100,
    0b00100,
    0b01110,
    0b01110,
    0b10111,
    0b11111,
    0b01110,
    0b00000
  ]
  lcd.add_character(drop_character, 3)

  while(True):
    try:
      archive.refresh()
      last_entry = archive.last_entry()
      last_entry.open()

      time=last_entry.dataframe.index[-1]
      temperature = last_entry.dataframe["temperature"].iloc[-1]
      humidity = last_entry.dataframe["humidity"].iloc[-1]

      last_entry.close()

      lcd.clear()
      lcd.print(f"\00{time.strftime('%H:%M')}")
      lcd.set_position(1,0)
      lcd.print(f"\02{temperature:4.1f}\01C \03{humidity:2.0f}% ")
    except:
      pass
    sleep(10)
