from scd4x import SCD4X

class Sensor_SCD4X:
  Parameters = ["temperature", "humidity", "co2"]
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
    "co2":{
      "name":"CO₂",
      "color":"#222222",
      "format":"0.0f",
      "suffix":"ppm"
    }
  }

  def __init__(self):
    self.scd = SCD4X()
    self.scd.start_periodic_measurement()

  def measure(self):
    co2, temperature, rh, _ = self.scd.measure()
    return [temperature, rh, co2]
