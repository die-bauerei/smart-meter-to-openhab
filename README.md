# smart-meter-to-openhab
Pushing data of ISKRA MT175 smart meter to openhab. 
For a connection to the Smart meter you need a USB infrared adapter. There are several adapters on the market (e.g. https://weidmann-elektronik.de/Produkt_IR-Kopf.html) that just need to be pluged in. They are usually detected as a casual serial port (/dev/ttyUSB0)

## Installation ##
The python package can be installed from PyPi (https://pypi.org/project/smart-meter-to-openhab/)
It as advisable to use the same python version as specfied in the pyproject.toml.
Follow the process in *install-poetry.sh* 

1. Navigate to the folder where the virtual environment shall be created (e.g. your home dir):
```bash
cd ~
```
2. Create virtual environment (this will create a new folder *smart_meter_py_env*):
```bash
python3 -m venv smart_meter_py_env
```
3. Activate the virtual environment
```bash
source smart_meter_py_env/bin/activate
```
4. Upgrade pip and setuptools
```bash
python3 -m pip install --upgrade pip setuptools
```
5. Install smart-meter-to-openhab
```bash
pip install smart-meter-to-openhab
```
6. Provide environment variables. You can e.g. pass a .env file to smart-meter-to-openhab via the option *--dotenv_path*. Or provide them by any other means (e.g. in your ~/.profile).
```bash
# Hostname incl. http(s) (required)
OH_HOST='<http://your_ip:your_port'
#openhab user (or token) for login (optional)
OH_USER=''
#openhab password for login (optional)
OH_PASSWD=''
#current consumption openhab item (required)
OVERALL_CONSUMPTION_WATT_OH_ITEM='smart_meter_overall_consumption'
#other openhab item names (optional)
PHASE_1_CONSUMPTION_WATT_OH_ITEM='smart_meter_phase_1_consumption'
PHASE_2_CONSUMPTION_WATT_OH_ITEM='smart_meter_phase_2_consumption'
PHASE_3_CONSUMPTION_WATT_OH_ITEM='smart_meter_phase_3_consumption'
ELECTRICITY_METER_KWH_OH_ITEM='smart_meter_electricity_meter'
```
NOTE: certificate verification is turned off, in case *OH_HOST* refers to an https address (since most openHAB instances do probably use self-signed certificates)  

7. Run smart-meter-to-openhab with e.g.
```bash
nohup smart_meter_to_openhab --logfile ~/smart_meter.log --verbose &
```

## Autostart after reboot and on failure ##
Create a systemd service by opening the file */etc/systemd/system/smart_meter_to_openhab.service* and copy paste the following contents. Replace User/Group/ExecStart accordingly. 
```bash
[Unit]
Description=smart_meter_to_openhab
Documentation=https://github.com/die-bauerei/smart-meter-to-openhab
After=network-online.target

[Service]
Type=simple
User=openhab
Group=openhab
UMask=002
Restart=always
RestartSec=5s
ExecStart=/usr/bin/bash -lc "/home/openhab/smart_meter_py_env/bin/smart_meter_to_openhab --logfile /home/openhab/smart_meter.log --verbose"

[Install]
WantedBy=multi-user.target
```

Now execute the following commands to enable autostart:
```bash
sudo systemctl --system daemon-reload
sudo systemctl enable smart_meter_to_openhab.service
```

It is now possible to start, stop, restart and check the status of smart-meter-to-openhab with:
```bash
sudo systemctl start smart_meter_to_openhab.service
sudo systemctl stop smart_meter_to_openhab.service
sudo systemctl restart smart_meter_to_openhab.service
sudo systemctl status smart_meter_to_openhab.service
```

## Development ##
Development is done in wsl2 on ubuntu 22.04.
Setting up the development environment on Windows is not supported. But in principal it could be setup as well since no OS specific functionalities are used.

### Setup ###
The project is using [poetry](https://python-poetry.org/) for managing packaging and resolve dependencies.
To install poetry call *install-poetry.sh*. This will install poetry itself as well as python and the required packages as a virtual environment in *.venv*.
Example settings for development in VS Code are provided in *vscode-settings*. (Copy them to *.vscode* folder)
Follow these [instructions](https://docs.pydantic.dev/latest/integrations/visual_studio_code/) to enable proper linting and type checking. 