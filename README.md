# smart-meter-to-openhab
Pushing data of ISKRA MT175 smart meter to openhab

## Installation ##
The python package can be downloaded from the github releases (e.g. *smart_meter_to_openhab-0.1.0.tar.gz*)
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
5. Install smart_meter_to_openhab
```bash
pip install smart_meter_to_openhab-0.1.0.tar.gz
```
6. Configure smart_meter_to_openhab
```bash
cd ~/smart_meter_py_env/lib/python3.11/site-packages/smart_meter_to_openhab
# add your values to the file .env.example and change the name to .env
mv .env.example .env
```
7. Run smart_meter_to_openhab with e.g.
```bash
nohup python ~/smart_meter_py_env/lib/python3.11/site-packages/smart_meter_to_openhab_scripts/main.py --logfile ~/smart_meter.log --verbose &
```

## Development ##
Development is done in wsl2 on ubuntu 20.4.
Setting up the development environment on Windows is not supported. But in principal it could be setup as well since no OS specific functionalities are used.

### Setup ###
The project is using [poetry](https://python-poetry.org/) for managing packaging and resolve dependencies.
To install poetry call *install-poetry.sh*. This will install poetry itself as well as python and the required packages as a virtual environment in *.venv*.
Example settings for development in VS Code are provided in *vscode-settings*. (Copy them to *.vscode* folder)
Follow these [instructions](https://docs.pydantic.dev/latest/integrations/visual_studio_code/) to enable proper linting and type checking. 