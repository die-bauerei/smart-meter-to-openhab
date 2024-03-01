import os
from pathlib import Path
package_path=Path(__file__).parent.parent.absolute()
from dotenv import load_dotenv
if os.path.isfile(f"{package_path}/.env"):
    load_dotenv(dotenv_path=f"{package_path}/.env")