import time
import RPi.GPIO as GPIO

class hd44780:
  E_PULSE = 0.0005
  E_DELAY = 0.0005

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

  def set_position(self, row, col):
    if col < 0 or col > 15 or row < 0 or row > 1:
      raise ValueError(f"Invalid position: {row},{col}")
    if row == 0:
      address = 0x80 + col
    elif row == 1:
      address = 0xC0 + col
    self.send_instruction(address)

  def add_character(self, character, index):
    if index < 0 or index > 8:
      raise ValueError(f"Invalid index: {index}")
    if len(character) != 8:
      raise ValueError(f"Invalid character size")
    self.send_instruction(0x40 + index * 8)
    for row in character:
      self.send_byte(row)

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

  def __init__(self, pinmap):
    self.pinmap=pinmap
    self.data_pins={key:value for key, value in self.pinmap.items() if key.startswith("D")}
    self.setup_gpio()
    self.init_display()

if __name__ == '__main__':
  disp=hd44780(hd44780.default_pinmap)

  disp.print("This is a test")

  custom_char=[0b10101, 0b01010, 0b10101, 0b01010, 0b10101, 0b01010, 0b10101, 0b01010]
  disp.add_character(custom_char, 0)
  disp.set_position(1,6)
  disp.print("\x00\x00\x00")
