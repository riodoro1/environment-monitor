import time
import RPi.GPIO as GPIO

class HD44780:
  E_PULSE = 0.0005
  E_DELAY = 0.0005
  ROWS = 2
  COLUMNS = 16

  default_pinmap={
    "RS":4,
    "E":17,
    "D4":18,
    "D5":22,
    "D6":23,
    "D7":24,
  }

  def write(self, byte):
    def write_bit(byte, bit):
      pin = bit if bit >= 4 else bit + 4
      pin_value = GPIO.HIGH if byte & 1 << bit else GPIO.LOW
      GPIO.output(self.data_pins[f"D{pin}"], pin_value)

    def pulse_enable():
      time.sleep(self.E_DELAY)
      GPIO.output(self.pinmap["E"], GPIO.HIGH)
      time.sleep(self.E_PULSE)
      GPIO.output(self.pinmap["E"], GPIO.LOW)
      time.sleep(self.E_DELAY)

    for bit in range(4,8):
      write_bit(byte, bit)
    pulse_enable()

    for bit in range(0,4):
      write_bit(byte, bit)
    pulse_enable()

  def send_instruction(self, byte):
    GPIO.output(self.pinmap["RS"], GPIO.LOW)
    self.write(byte)

  def send_byte(self, byte):
    GPIO.output(self.pinmap["RS"], GPIO.HIGH)
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
    if col < 0 or col > self.columns-1 or row < 0 or row > self.rows-1:
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

  def setup_gpio(self):
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(list(self.pinmap.values()), GPIO.OUT)

  def init_display(self):
    self.send_instruction(0x33)
    self.send_instruction(0x32) #First, make sure the LCD is in 8 bit mode
    self.send_instruction(0x28) #4 bit 2 lines
    self.send_instruction(0x0C) #Display ON, Cursor OFF, Blink OFF
    self.send_instruction(0x06) #Increment address upon write, no shift
    self.clear()
    self.custom_chars = 0 #Adding new characters will overwrite old ones.

  def __init__(self, pinmap = self.default_pinmap):
    self.pinmap=pinmap
    self.data_pins={key:value for key, value in self.pinmap.items() if key.startswith("D")}
    self.rows = self.ROWS
    self.columns = self.COLUMNS
    self.setup_gpio()
    self.init_display()
