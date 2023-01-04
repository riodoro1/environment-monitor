import os
import time
from datetime import datetime
import threading

from hd44780 import hd44780
from measurer import MeasurementsArchive
from sensor import Sensor

class Display(threading.Thread):
  COLUMNS = 2

  class Element:
    def __init__(self, key, format_string):
      self.key = key
      self.format_string = format_string
      self.text = ""
      self.previous_text = ""

    def set_value(self, value):
      self.previous_text = self.text
      self.text = self.format_string.format(value = value)

  def __init__(self, lcd, archive):
    self.lcd = lcd
    self.archive = archive
    self.elements = []

    self.add_time_element()
    self.add_elements(Sensor.Decorations)

  def add_time_element(self):
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
    self.lcd.add_character(clock_character) # Now at index 0
    self.elements.append(Display.Element("", "\00{value}"))

  def add_elements(self, parameter_decorations):
    def add_custom_chars(decoration):
      index = 0;
      format_substitutions = []
      for custom_char in decoration["display"]["custom_chars"]:
        new_index = lcd.add_character(custom_char)
        format_substitutions.append((chr(index), chr(new_index)))
        index += 1
      format_string = decoration["display"]["format"]
      for substitution in reversed(format_substitutions):
        format_string = format_string.replace(substitution[0], substitution[1])
      return format_string

    for key, decoration in parameter_decorations.items():
      format_string = add_custom_chars(decoration)
      self.elements.append(Display.Element(key, format_string))

  def redraw(self):
    row = 0
    col = 0
    for element in self.elements:
      if element.text != element.previous_text:
        self.lcd.set_position(row, int(col * self.lcd.columns/self.COLUMNS))
        self.lcd.print(element.text.ljust(len(element.previous_text), " "))
        element.previous_text = element.text

      col += 1
      if(col > self.COLUMNS - 1):
        col = 0
        row += 1

  def run(self):
    self.lcd.clear()
    self.archive.open()

    prev_last_entry = None
    while(True):
      archive.refresh()
      last_entry = archive.last_entry()

      if last_entry != prev_last_entry:
        last_entry.open()

        last_entry_time = last_entry.dataframe.index[-1]
        display.elements[0].set_value(last_entry_time.strftime("%H:%M"))
        for element in display.elements[1:]:
          element.set_value(last_entry.dataframe[element.key].iloc[-1])

        display.redraw()
        last_entry.close()
        prev_last_entry = last_entry

      time.sleep(5)

if __name__ == "__main__":
  archive_path = os.environ.get("MEASUREMENTS_PATH")

  if archive_path:
    archive = MeasurementsArchive(archive_path)
  else:
    raise RuntimeError("No archive path in environment")

  lcd = hd44780(hd44780.default_pinmap)
  display = Display(lcd, archive)

  display.run()
