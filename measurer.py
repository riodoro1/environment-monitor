
import time
import math

import threading
import bme280
from smbus import SMBus
from bme280 import BME280
import pandas as pd
import numpy as np
from datetime import datetime
import os, tempfile, itertools, random, string

class MeasurementsArchive:
  class ArchiveEntry:
    column_names=["temperature", "humidity", "pressure"]

    def __init__(self, path, start, end, samples, dataframe):
      self.path=path
      self.start=start
      self.end=end
      self.samples=samples
      self.dataframe=dataframe

    @classmethod
    def from_file(cls, path):
      def check_dataframe(df):
        return (list(df.columns)==cls.column_names and
                type(df.index)==pd.DatetimeIndex)
      df=pd.read_pickle(path)
      if not check_dataframe(df):
        raise ValueError("DataFrame has invalid format")
      return cls( path=path,
                  start=df.first_valid_index().to_pydatetime() if len(df)>0 else None,
                  end=df.last_valid_index().to_pydatetime() if len(df)>0 else None,
                  samples=df.shape[0],
                  dataframe=None)

    @classmethod
    def empty(cls, directory):
      def random_file(directory, length=8):
        path=os.path.join(directory, "".join(random.choices(string.ascii_lowercase, k=length)))
        return path if not os.path.exists(path) else random_file(directory, length)

      path=random_file(directory)
      pd.DataFrame( [], columns=cls.column_names, 
                      dtype=np.float64, 
                      index=pd.DatetimeIndex([], name="time")).to_pickle(path)
      return cls( path=path,
                  start=None,
                  end=None,
                  samples=0,
                  dataframe=None)

    def __repr__(self) -> str:
        return f"measurer.MeasurementsArchive.ArchiveEntry(path=\"{self.path}\", start={repr(self.start)}, end={repr(self.end)}, samples={self.samples}, dataframe=None)"

    def __str__(self) -> str:
        return f"ArchiveEntry from {self.start} to {self.end}. Samples: {self.samples}"

    def has_timeframe(self):
      return self.start is not None and self.end is not None

    def overlapping(self, start, end):
      return self.start <= end and self.end >= start

    def overlapping_other(self, other):
      if not self.has_timeframe() or not other.has_timeframe():
        return False
      return self.overlapping(other.start, other.end)

    def is_open(self):
      return self.dataframe is not None

    def open(self):
      self.dataframe=pd.read_pickle(self.path)

    def save(self):
      if not self.is_open():
        raise RuntimeError("Cannot save a closed ArchiveEntry")
      self.dataframe.to_pickle(self.path)

    def close(self):
      if self.is_open():
        self.save()
      self.dataframe=None

    def append_measurement(self, measurement, time):
      if not self.is_open():
        raise RuntimeError("Cannot append to a closed ArchiveEntry")
      if not self.end is None and self.end > time:
        raise RuntimeError(f"Appending measurement with time: {time} which is before end time: {self.end}")
      frame=pd.DataFrame( [measurement], 
                          columns=MeasurementsArchive.ArchiveEntry.column_names,
                          index=pd.DatetimeIndex([time], name="time")
      )
      self.dataframe=pd.concat([self.dataframe, frame], copy=False, verify_integrity=True)
      self.samples+=1
      self.end=time

  def __init__(self, archive_path):
    self.archive_path=archive_path
    self.archive_entries=[]
  
  def last_entry(self):
    return self.archive_entries[-1]

  def is_open(self):
    return len(self.archive_entries) != 0

  def open(self):
    if self.is_open():
      self.close()

    if not os.path.isdir(self.archive_path):
      try:
        os.mkdir(self.archive_path)
      except Exception as e:
        self.archive_path=tempfile.mkdtemp()
        print(f"Failed to create archive directory: {e}\nWill write to: {self.archive_path}")

    files_in_archive_path=[f for f in 
                          [os.path.join(self.archive_path, f) for f in os.listdir(self.archive_path)]
                          if os.path.isfile(f)]

    for file in files_in_archive_path:
      try:
        self.archive_entries.append(MeasurementsArchive.ArchiveEntry.from_file(file))
      except:
        print(f"{file} not a valid pandas DataFrame")

    self.archive_entries.sort(key=lambda e:e.start if not e.start is None else datetime.max)

    for a, b in itertools.combinations(self.archive_entries, 2):
      if a.overlapping_other(b):
        print(f"{a.path} and {b.path} are overlapping!")

    archive_entries_ending_in_future=(e for e in self.archive_entries if not e.end is None and e.end > datetime.now())
    for e in archive_entries_ending_in_future:
      self.archive_entries.remove(e)
      print(f"{e.path} is ending in the future.")

    if not self.archive_entries:
      self.append_entry()
  
  def close(self):
    open_entries = (e for e in self.archive_entries if e.is_open())
    for entry in open_entries:
      entry.close()
    self.archive_entries=[]
    
  def append_entry(self):
    try:
      if self.last_entry().is_open():
        self.last_entry().close()
    except:
      pass
    finally:
      self.archive_entries.append(MeasurementsArchive.ArchiveEntry.empty(self.archive_path))

  def entries_in_span(self, start, end):
    entries=[]
    for e in self.archive_entries:
      if e.overlapping(start, end):
        entries.append(e)
    return entries

class Measurer(threading.Thread):
  def __init__(self, bme280, archive, period=60, max_samples_per_file=1000000, save_every_samples=5):
    self.bme280=bme280
    self.archive=archive
    self.period=period

    self.max_samples_per_file=max_samples_per_file
    self.save_every_samples=save_every_samples
    self.appends_since_store=0

    self.stop_event=threading.Event()
    threading.Thread.__init__(self)

  def make_measurement(self):
    self.bme280.update_sensor()
    self.append_to_archive(
      [
        self.bme280.temperature,
        self.bme280.humidity,
        self.bme280.pressure
      ], 
      datetime.now()
    )

  def append_to_archive(self, measurement, time):
    try:
      last_entry=self.archive.last_entry()
    except:
      raise RuntimeError("Cannot append to an empty MeasurementsArchive, perhaps it's unopened?")

    if not last_entry.is_open():
      last_entry.open()

    last_entry.append_measurement(measurement, time)

    self.appends_since_store+=1
    if self.appends_since_store > self.save_every_samples:
      last_entry.save()
      self.appends_since_store=0

    if last_entry.samples > self.max_samples_per_file:
      self.archive.append_entry()

  def stop(self):
    self.stop_event.set()
    self.archive.close()

  def run(self):
    while not self.stop_event.is_set():
      self.make_measurement()
      time.sleep(self.period)

def obtain_bme(smbus=1):
  bus = SMBus(smbus)
  bme = BME280(i2c_dev=bus)
  bme.update_sensor()
  time.sleep(2)
  bme.update_sensor()
  time.sleep(2)
  return bme

if __name__ == "__main__":
  period=30
  save_every=10
  samples_in_hour=3600/period
  samples_in_day=24*samples_in_hour
  max_samples=1*samples_in_day
  a=MeasurementsArchive("/home/rafal/climate-monitor/measurements")
  a.open()
  m=Measurer(obtain_bme(), a, period, max_samples_per_file=max_samples, save_every_samples=save_every)
  print("Running a test instance of measurer")
  m.start()