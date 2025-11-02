from smbus import SMBus
from bme280 import BME280
import time

class Sensor_BME280:
  Parameters = ["temperature", "humidity", "pressure"]
  Decorations = {
    "temperature":{
      "name":"Temperature",
      "color":"#EF553B",
      "format":"0.1f",
      "suffix":"°C",
      "display":{
        "custom_chars":[
          [
            0b00100,
            0b01010,
            0b01010,
            0b01110,
            0b11111,
            0b11111,
            0b01110,
            0b00000
          ],
          [
            0b00110,
            0b01001,
            0b01001,
            0b00110,
            0b00000,
            0b00000,
            0b00000,
            0b00000
          ]
        ],
        "format":"\00{value:4.1f}\01C"
      }
    },
    "humidity":{
      "name":"Humidity",
      "color":"#636EFA",
      "format":"0.0f",
      "suffix":"%",
      "display":{
        "custom_chars":[
          [
            0b00100,
            0b00100,
            0b01110,
            0b01110,
            0b10111,
            0b11111,
            0b01110,
            0b00000
          ]
        ],
        "format":"\00{value:2.0f}%"
      }
    },
    "pressure":{
      "name":"Pressure",
      "color":"#00CC96",
      "format":"0.0f",
      "suffix":"hPa",
      "display":{
        "custom_chars":[
          [
            0b11010,
            0b10010,
            0b11010,
            0b10010,
            0b11010,
            0b10111,
            0b11010,
            0b00000
          ]
        ],
        "format":"\00{value:.0f}hPa"
      }
    },
  }

  def __init__(self, smbus=1):
    bus = SMBus(smbus)
    self.bme = BME280(i2c_dev=bus)
    self.bme.update_sensor()
    time.sleep(2)
    self.bme.update_sensor()
    time.sleep(2)

  def measure(self):
    self.bme.update_sensor()
    return [self.bme.temperature, self.bme.humidity, self.bme.pressure]
