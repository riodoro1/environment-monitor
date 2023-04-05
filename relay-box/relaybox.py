import json
import sys
from fsgpio import FsGpio

class RelayBox:
  def __init__(self, configPath):
    self.data = None
    with open(configPath, "r") as f:
      self.data = json.load(f)

  def setUpGpio(self):
    for outlet in self.data["outlets"]:
      pin = FsGpio(outlet["GPIO"]["pin"])
      pin.export()
      pin.setDirection(pin.OUT)

  def byId(self, id):
    return next((outlet for outlet in self.data["outlets"] if outlet['id'] == id), None)

  def byName(self, name):
    return next((outlet for outlet in self.data["outlets"] if outlet['name'] == name), None)

  def turnOn(self, outlet):
    if outlet:
      FsGpio(outlet["GPIO"]["pin"]).setValue(outlet["GPIO"]["on-state"])

  def turnOff(self, outlet):
    if outlet:
      offState = 1 if outlet["GPIO"]["on-state"] == 0 else 0
      FsGpio(outlet["GPIO"]["pin"]).setValue(offState)

if __name__ == "__main__":
  relayBox = RelayBox(sys.argv[1])
  relayBox.setUpGpio()

  for arg in sys.argv[2:]:
    id, state = arg.split(":")
    outlet = None

    if id.isdigit():
      if byId := relayBox.byId(int(id)):
        outlet = byId
    if byName := relayBox.byName(id):
      outlet = byName

    if not outlet:
      print(f"No outlet identifiable by {outlet}")
      exit(1)

    if state.lower() == "on":
      relayBox.turnOn(outlet)
    elif state.lower() == "off":
      relayBox.turnOff(outlet)
    else:
      print(f"Invalid requested state: {state}")
      exit(2)
