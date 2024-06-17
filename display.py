import os
import time
from datetime import datetime
import threading
import json

from hd44780_over_pcf8574 import HD44780
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

  def __init__(self, lcd, archive_path):
    self.lcd = lcd
    self.measurer_status_path = os.path.join(archive_path, "status.json")
    self.elements = []
    self.init_display()

  def init_display(self):
    self.lcd.init_display()
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
      if "display" in decoration:
        format_string = add_custom_chars(decoration)
        self.elements.append(Display.Element(key, format_string))

  def invalidate_elements(self):
    for element in self.elements:
      element.previous_text = "\21\37"

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

    last_timestamp = None
    redraws_since_init = 0
    while(True):
      try:
        with open(self.measurer_status_path) as measurer_status:
          json_dict = json.load(measurer_status)
          timestamp = datetime.fromisoformat(json_dict["time"])

        if timestamp != last_timestamp:
          self.elements[0].set_value(timestamp.strftime("%H:%M"))

          for element in self.elements[1:]:
            element.set_value(json_dict[element.key])

          if redraws_since_init > 10:
            self.init_display()
            self.invalidate_elements()
            redraws_since_init = 0

          self.redraw()
          redraws_since_init += 1
          last_timestamp = timestamp
      except JSONDecodeError:
        print(f"Empty measurer status file {self.measurer_status_path}, will retry")
      time.sleep(5)

if __name__ == "__main__":
  archive_path = os.environ.get("MEASUREMENTS_PATH")

  lcd = HD44780()
  display = Display(lcd, archive_path)

  display.run()
