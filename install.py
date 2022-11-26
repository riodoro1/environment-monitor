#!./venv/bin/python

import re, os, subprocess
from pathlib import Path

SERVICE_DEST = "/etc/systemd/system"

def subst_environ(str):
  re_pattern="<([A-Z_]+)>"
  while True:
    m = re.search(re_pattern, str)
    if m == None:
      break
    str = str[:m.start()] + os.environ.get(m.group(1)) + str[m.end():]
  return str

def create_service_units():
  installed = []
  try:
    for template in os.scandir("services"):
      file = open(template, "r")
      content = file.read()
      service_name = Path(template.path).stem
      cmd = f"echo \"{subst_environ(content)}\" | sudo tee {SERVICE_DEST}/{service_name} > /dev/null"
      print(f"Installing unit {service_name} in {SERVICE_DEST}")
      subprocess.call(cmd, shell=True)
      installed.append(service_name)
  except FileNotFoundError:
    print("Are you running from environment-monitor dir?")
  return installed

if __name__ == "__main__":
  installed_services = create_service_units()
  print(f"Reloading systemd")
  subprocess.call("sudo systemctl daemon-reload", shell=True)
  for service in installed_services:
    print(f"Enabling and starting {service}")
    subprocess.call(f"sudo systemctl enable {service}", shell=True)
    subprocess.call(f"sudo systemctl start {service}", shell=True)
