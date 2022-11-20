#!./venv/bin/python

import re, os, subprocess
from pathlib import Path

def subst_environ(str):
  re_pattern="<([A-Z_]+)>"
  while True:
    m = re.search(re_pattern, str)
    if m == None:
      break
    str = str[:m.start()] + os.environ.get(m.group(1)) + str[m.end():]
  return str

def create_service_units():
  try:
    for template in os.scandir("services"):
      file = open(template, "r")
      content = file.read()
      cmd = f"echo \"{subst_environ(content)}\" | sudo tee /etc/systemd/system/{Path(template.path).stem} > /dev/null"
      subprocess.call(cmd, shell=True)
  except FileNotFoundError:
    print("Are you running from environment-monitor dir?")

if __name__ == "__main__":
  create_service_units()
  subprocess.call("sudo systemctl daemon-reload", shell=True)
