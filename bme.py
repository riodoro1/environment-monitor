from smbus import SMBus
from bme280 import BME280
import time

class Bme:
  Parameters = ["temperature", "humidity", "pressure"]
  Decorations = {
    "temperature":{
      "name":"Temperature",
      "color":"#EF553B",
      "format":"0.1f",
      "suffix":"°C"
    },
    "humidity":{
      "name":"Humidity",
      "color":"#636EFA",
      "format":"0.0f",
      "suffix":"%"
    },
    "pressure":{
      "name":"Pressure",
      "color":"#00CC96",
      "format":"0.0f",
      "suffix":"hPa"
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
