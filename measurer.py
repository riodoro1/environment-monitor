import pandas as pd
import numpy as np

import datetime, threading, signal, os, tempfile, itertools, random, string, sys, json

from sensor import Sensor

class MeasurementsArchive:
  class ArchiveEntry:
    column_names=Sensor.Parameters

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

    def __eq__(self, other):
      if not isinstance(other, self.__class__):
        return False

      return self.path == other.path and self.start == other.start and self.end == other.end and self.samples == other.samples


    def has_timeframe(self):
      return self.start is not None and self.end is not None

    def overlapping(self, start, end):
      return self.has_timeframe() and self.start <= end and self.end >= start

    def overlapping_other(self, other):
      return other.has_timeframe() and self.overlapping(other.start, other.end)

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
      if self.start is None:
        self.start = self.end

  def __init__(self, archive_path):
    self.archive_path=archive_path
    self.archive_entries=[]

  def last_entry(self):
    return self.archive_entries[-1]

  def archive_start(self):
    return self.archive_entries[0].start

  def archive_end(self):
    return self.last_entry().end

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

    self.append_entries_from_files(files_in_archive_path)

    if not self.archive_entries:
      self.append_entry()

  def refresh_last_entry(self):
    self.last_entry().close()
    last_entry_path=self.last_entry().path
    self.archive_entries.pop()
    self.archive_entries.append(MeasurementsArchive.ArchiveEntry.from_file(last_entry_path))

  def refresh(self):
    if not self.is_open():
      raise RuntimeError("Cannot refresh an unopend MeasurementsArchive")

    self.refresh_last_entry()

    already_opened_files=[e.path for e in self.archive_entries]
    new_files=[f for f in
              [os.path.join(self.archive_path, f) for f in os.listdir(self.archive_path)]
              if os.path.isfile(f) and f not in already_opened_files]
    if new_files:
      self.append_entries_from_files(new_files)

  def is_open(self):
    return len(self.archive_entries) != 0

  def close(self):
    open_entries = (e for e in self.archive_entries if e.is_open())
    for entry in open_entries:
      entry.close()
    self.archive_entries=[]

  def append_entry(self):
    try:
      self.last_entry().close()
    except:
      pass
    finally:
      self.archive_entries.append(MeasurementsArchive.ArchiveEntry.empty(self.archive_path))

  def append_entries_from_files(self, filepaths):
    for file in filepaths:
      try:
        self.archive_entries.append(MeasurementsArchive.ArchiveEntry.from_file(file))
      except:
        print(f"{file} not a valid pandas DataFrame")

    self.archive_entries.sort(key=lambda e:e.start if not e.start is None else datetime.datetime.max)

    for a, b in itertools.combinations(self.archive_entries, 2):
      if a.overlapping_other(b):
        print(f"{a.path} and {b.path} are overlapping!") # perhaps a RuntimeError

    archive_entries_ending_in_future=(e for e in self.archive_entries if not e.end is None and e.end > datetime.datetime.now())
    for e in archive_entries_ending_in_future:
      self.archive_entries.remove(e)
      print(f"{e.path} is ending in the future.") # perhaps a RuntimeError

  def entries_in_span(self, start, end):
    entries=[]
    for e in self.archive_entries:
      if e.overlapping(start, end):
        entries.append(e)
    return entries

class Measurer(threading.Thread):
  def __init__(self, archive_path, period=60, max_samples_per_file=1000000, save_every_samples=5):
    self.sensor = Sensor()

    self.archive_path=archive_path
    self.archive=MeasurementsArchive(archive_path)

    self.period=period

    self.max_samples_per_file=max_samples_per_file
    self.save_every_samples=save_every_samples
    self.appends_since_store=0

    self.stop_event=threading.Event()
    threading.Thread.__init__(self)

  def make_measurement(self):
    time = datetime.datetime.now()
    measurement = self.sensor.measure()
    self.append_to_archive(measurement, time)
    self.write_status(measurement, time)

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

  def write_status(self, measurement, time):
    json_dict = {"time":time.isoformat()}
    for index, parameter_name in enumerate(Sensor.Parameters):
      json_dict[parameter_name] = measurement[index]
    with open(self.status_file_path, "w") as status_file:
      json.dump(json_dict, status_file)
      status_file.close()

  def stop(self):
    self.stop_event.set()
    self.archive.close()
    os.unlink(self.status_file_path)

  def run(self):
    self.archive.open()
    self.status_file_path = os.path.join(self.archive_path, "status.json")
    if os.path.exists(self.status_file_path):
      print(f"{self.status_file_path} exists! This might mean there are two instances running or previous instance exited unexpectedly.")

    while True:
      self.make_measurement()
      if self.stop_event.wait(timeout = self.period):
        break

if __name__ == "__main__":
  PERIOD=30
  SAVE_EVERY=2
  SAMPLES_IN_HOUR=3600/PERIOD
  SAMPLES_IN_DAY=24*SAMPLES_IN_HOUR
  MAX_SAMPLES=7*SAMPLES_IN_DAY

  archive_path = os.environ.get("MEASUREMENTS_PATH")

  measurer=Measurer(archive_path, PERIOD, max_samples_per_file=MAX_SAMPLES, save_every_samples=SAVE_EVERY)

  def catch_signal(*args):
    measurer.stop()

  signal.signal(signal.SIGTERM, catch_signal)
  signal.signal(signal.SIGINT, catch_signal)
  print(f"Running in {measurer.archive.archive_path}...")
  measurer.run() # Can be blocking here, we are in a deamon thread after all
  print("Measurer stopped.")
