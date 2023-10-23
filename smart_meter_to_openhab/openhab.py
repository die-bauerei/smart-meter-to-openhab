import requests
import http
from logging import Logger
from requests.auth import HTTPBasicAuth
from typing import List
from .interfaces import SmartMeterValues, OhItemAndValue, create_smart_meter_values

class OpenhabConnection():
    def __init__(self, oh_host : str, oh_user : str, oh_passwd : str, logger : Logger) -> None:
        self._oh_host=oh_host
        self._session=requests.Session()
        self._session.auth=HTTPBasicAuth(oh_user, oh_passwd)
        self._session.headers={'Content-Type': 'text/plain'}
        self._logger=logger

    def post_to_items(self, values : SmartMeterValues) -> None:
        for v in values.convert_to_list():
            if v.value is not None: 
                with self._session.post(url=f"{self._oh_host}/rest/items/{v.oh_item}", data=str(v.value)) as response:
                   if response.status_code != http.HTTPStatus.OK:
                        self._logger.warning(f"Failed to post value to openhab item {v.oh_item}. Return code: {response.status_code}. text: {response.text})")

    def get_from_items(self, oh_items : List[str]) -> SmartMeterValues:
        values : List[OhItemAndValue] = []
        for item in oh_items:
            with self._session.get(url=f"{self._oh_host}/rest/items/{item}/state") as response:
                    if response.status_code != http.HTTPStatus.OK:
                        self._logger.warning(f"Failed to get value from openhab item {item}. Return code: {response.status_code}. text: {response.text})")
                    else:
                        values.append(OhItemAndValue(item, response.text.split()[0]))
        return create_smart_meter_values(values)