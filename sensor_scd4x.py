from scd4x import SCD4X

class Sensor_SCD4X:
  Parameters = ["temperature", "humidity", "co2"]
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
    "co2":{
      "name":"CO₂",
      "color":"#222222",
      "format":"0.0f",
      "suffix":"ppm",
      "display":{
        "custom_chars":[
          [
            0b00100,
            0b01010,
            0b00100,
            0b01110,
            0b00100,
            0b01010,
            0b00100,
            0b00000
          ]
        ],
        "format":"\00{value:3.0f}ppm"
      }
    }
  }

  def __init__(self):
    self.scd = SCD4X()
    self.scd.start_periodic_measurement()

  def measure(self):
    co2, temperature, rh, _ = self.scd.measure()
    return [temperature, rh, co2]
