import os.path
from time import sleep

class FsGpio:
  IN = "in"
  OUT = "out"
  HIGH = "1"
  LOW = "0"

  def __init__(self, pin):
    self.pin = pin
    self.exportPath = "/sys/class/gpio/export"
    self.unexportPath = "/sys/class/gpio/unexport"
    self.basePath = f"/sys/class/gpio/gpio{pin}"
    self.directionPath = f"{self.basePath}/direction"
    self.valuePath = f"{self.basePath}/value"

  def __fileWrite(self, path, str):
    with open(path, "w") as f:
      f.write(str)

  def __fileRead(self, path) -> str:
    with open(path, "r") as f:
      return f.read()

  def isExported(self):
    return os.path.isdir(self.basePath)

  def export(self):
    if not self.isExported():
      self.__fileWrite(self.exportPath, f"{self.pin}")
      sleep(0.5)

  def unexport(self):
    if self.isExported():
      self.__fileWrite(self.unexportPath, f"{self.pin}")

  def setDirection(self, direction):
    if not self.getDirection() == direction:
      self.__fileWrite(self.directionPath, direction)

  def getDirection(self):
    return self.__fileRead(self.directionPath)[:-1]

  def setValue(self, value):
    self.__fileWrite(self.valuePath, f"{value}")

  def getValue(self) -> str:
    return self.__fileRead(self.valuePath)[:-1]

  def setHigh(self):
    self.setValue(self.HIGH)

  def isHigh(self) -> bool:
    return self.getValue() == self.HIGH

  def setLow(self):
    self.setValue(self.LOW)

  def isLow(self) -> bool:
    return self.getValue() == self.LOW
