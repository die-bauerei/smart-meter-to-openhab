import requests
import http
import datetime
from logging import Logger
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter, Retry
from typing import List, Tuple
from .interfaces import *

# disable warnings about insecure requests because ssl verification is disabled
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class OpenhabConnection():
    def __init__(self, oh_host : str, oh_user : str, oh_passwd : str, logger : Logger) -> None:
        self._oh_host=oh_host
        self._session=requests.Session()
        if oh_user:
            self._session.auth=HTTPBasicAuth(oh_user, oh_passwd)
        retries=Retry(total=8,
                backoff_factor=0.1,
                status_forcelist=[ 500, 502, 503, 504 ])
        self._session.mount('http://', HTTPAdapter(max_retries=retries))
        self._session.mount('https://', HTTPAdapter(max_retries=retries))
        self._session.headers={'Content-Type': 'text/plain'}
        self._logger=logger

    def post_to_items(self, value_container : OhItemAndValueContainer) -> None:
        for v in value_container:
            if v.value is not None and v.oh_item:
                try:
                    with self._session.post(url=f"{self._oh_host}/rest/items/{v.oh_item}", data=str(v.value), verify=False) as response:
                        if response.status_code != http.HTTPStatus.OK:
                            self._logger.warning(f"Failed to post value to openhab item {v.oh_item}. Return code: {response.status_code}. text: {response.text})")
                except requests.exceptions.RequestException as e:
                    self._logger.warning("Caught Exception while posting to openHAB: " + str(e))

    def get_item_value_list_from_items(self, oh_item_names : Tuple[str, ...]) -> List[OhItemAndValue]:
        values : List[OhItemAndValue] = []
        for item in oh_item_names:
            if item:
                oh_item_value=OhItemAndValue(item)
                try:
                    with self._session.get(url=f"{self._oh_host}/rest/items/{item}/state", verify=False) as response:
                        if response.status_code != http.HTTPStatus.OK:
                            self._logger.warning(f"Failed to get value from openhab item {item}. Return code: {response.status_code}. text: {response.text})")
                        else:
                            oh_item_value=OhItemAndValue(item, float(response.text.split()[0]))
                except requests.exceptions.RequestException as e:
                    self._logger.warning("Caught Exception while getting from openHAB: " + str(e))
                values.append(oh_item_value)
        return values

    def get_values_from_items(self) -> SmartMeterValues:
        return SmartMeterValues.create(self.get_item_value_list_from_items(SmartMeterValues.oh_item_names()))

    # NOTE: This can potentially return values, although no new values have been posted. Depending on the config: 
    # https://www.openhab.org/docs/configuration/persistence.html
    def _get_persistence_values(self, oh_item_names : Tuple[str, ...], start_time : datetime.datetime, end_time : datetime.datetime) -> PersistenceValuesType:
        pers_values = []
        for item in oh_item_names:
            if item:
                values=[]
                try:
                    with self._session.get(
                        url=f"{self._oh_host}/rest/persistence/items/{item}", 
                        params={'starttime': start_time.isoformat(), 'endtime': end_time.isoformat()},
                        verify=False) as response:
                        if response.status_code != http.HTTPStatus.OK:
                            self._logger.warning(f"Failed to get persistence values from openhab item {item}. Return code: {response.status_code}. text: {response.text})")
                        else:
                            values=[float(data['state']) for data in response.json()['data']]
                except requests.exceptions.RequestException as e:
                    self._logger.warning("Caught Exception while getting persistence data from openHAB: " + str(e))
                pers_values.append(values)
        return pers_values

    def check_if_persistence_values_updated(self, start_time : datetime.datetime, end_time : datetime.datetime) -> bool:
        pers_values=self._get_persistence_values(SmartMeterValues.oh_item_names(), start_time, end_time)
        updated=SmartMeterValues.check_if_updated(pers_values)
        if not updated:
            self._logger.warning("Persistence values have not been updated.")
            for index, values in enumerate(pers_values):
                self._logger.warning(f"Values for index {index}: {values}")
        return updated