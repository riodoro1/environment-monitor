from smbus import SMBus
import time

class PCF8574:
  def __init__(self, address, bus = 1):
    self.bus = SMBus(bus)
    self.address = address
    self._read()

  def _read(self):
    self.output = self.bus.read_byte(self.address)

  def _write(self):
    self.bus.write_byte(self.address, self.output)

  def write(self, value):
    self.output = value
    self._write()

  def set_pin(self, pin, state):
    if pin not in range(0,16):
      raise ValueError("pin not in range!")
    self.output = self.output | 1 << pin if state else self.output & ~(1 << pin)
    self._write()

class HD44780:
  RS_PIN = 0
  RW_PIN = 1
  E_PIN = 2
  BACKLIGHT_PIN = 3

  E_DELAY = 0.0004
  E_PULSE = 0.00001

  ROWS = 2
  COLUMNS = 16

  def backlight_on(self):
    self.pcf.set_pin(self.BACKLIGHT_PIN, True)

  def backlight_off(self):
    self.pcf.set_pin(self.BACKLIGHT_PIN, False)

  def write(self, byte):
    def pulse_enable():
      time.sleep(self.E_DELAY)
      self.pcf.set_pin(self.E_PIN, True)
      time.sleep(self.E_PULSE)
      self.pcf.set_pin(self.E_PIN, False)
      time.sleep(self.E_DELAY)

    self.pcf.set_pin(self.RW_PIN, False)

    self.pcf.output = (byte & 0xf0) ^ (self.pcf.output & 0x0f)
    pulse_enable()
    byte = byte << 4
    self.pcf.output = (byte & 0xf0) ^ (self.pcf.output & 0x0f)
    pulse_enable()

  def send_instruction(self, byte):
    self.pcf.set_pin(self.RS_PIN, False)
    self.write(byte)

  def send_byte(self, byte):
    self.pcf.set_pin(self.RS_PIN, True)
    self.write(byte)

  def send_char(self, char):
    self.send_byte(ord(char))

  def print(self, str):
    for c in str[:16]:
      self.send_char(c)

  def clear(self):
    self.send_instruction(0x01)
    self.custom_chars = 0

  def set_position(self, row, col):
    if col < 0 or col > 15 or row < 0 or row > 1:
      raise ValueError(f"Invalid position: {row},{col}")
    if row == 0:
      address = 0x80 + col
    elif row == 1:
      address = 0xC0 + col
    self.send_instruction(address)

  def add_character(self, character):
    if self.custom_chars == 8:
      raise ValueError(f"Custom characters memory full")
    if len(character) != 8:
      raise ValueError(f"Invalid character size")

    index = self.custom_chars
    self.custom_chars += 1

    self.send_instruction(0x40 + index * 8)
    for row in character:
      self.send_byte(row)
    return index

  def init_display(self):
    self.send_instruction(0x33)
    self.send_instruction(0x32) #First, make sure the LCD is in 8 bit mode
    self.send_instruction(0x28) #4 bit 2 lines
    self.send_instruction(0x0C) #Display ON, Cursor OFF, Blink OFF
    self.send_instruction(0x06) #Increment address upon write, no shift
    self.clear()

  def __init__(self, address = 0x27, bus = 1):
    self.pcf = PCF8574(address, bus)
    self.init_display()
    self.backlight_on()
    self.rows = self.ROWS
    self.columns = self.COLUMNS
