import requests
import http
import datetime
from logging import Logger
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter, Retry
from typing import List, Tuple
from statistics import median
from .interfaces import *

class OpenhabConnection():
    def __init__(self, oh_host : str, oh_user : str, oh_passwd : str, logger : Logger) -> None:
        self._oh_host=oh_host
        self._session=requests.Session()
        if oh_user:
            self._session.auth=HTTPBasicAuth(oh_user, oh_passwd)
        retries=Retry(total=5,
                backoff_factor=0.1,
                status_forcelist=[ 500, 502, 503, 504 ])
        self._session.mount('http://', HTTPAdapter(max_retries=retries))
        self._session.headers={'Content-Type': 'text/plain'}
        self._logger=logger

    def post_to_items(self, value_container : OhItemAndValueContainer) -> None:
        for v in value_container.item_value_list():
            if v.value is not None and v.oh_item:
                try:
                    with self._session.post(url=f"{self._oh_host}/rest/items/{v.oh_item}", data=str(v.value)) as response:
                        if response.status_code != http.HTTPStatus.OK:
                            self._logger.warning(f"Failed to post value to openhab item {v.oh_item}. Return code: {response.status_code}. text: {response.text})")
                except requests.exceptions.RequestException as e:
                    self._logger.warning("Caught Exception while posting to openHAB: " + str(e))

    def get_item_value_list_from_items(self, oh_item_names : Tuple[str, ...]) -> List[OhItemAndValue]:
        values : List[OhItemAndValue] = []
        for item in oh_item_names:
            if item:
                try:
                    with self._session.get(url=f"{self._oh_host}/rest/items/{item}/state") as response:
                        if response.status_code != http.HTTPStatus.OK:
                            self._logger.warning(f"Failed to get value from openhab item {item}. Return code: {response.status_code}. text: {response.text})")
                        else:
                            values.append(OhItemAndValue(item, float(response.text.split()[0])))
                except requests.exceptions.RequestException as e:
                    self._logger.warning("Caught Exception while getting from openHAB: " + str(e))
                    values.append(OhItemAndValue(item))
        return values

    def get_values_from_items(self, oh_item_names : SmartMeterOhItemNames) -> SmartMeterValues:
        return SmartMeterValues.create(self.get_item_value_list_from_items(oh_item_names))
    
    def get_extended_values_from_items(self, oh_item_names : ExtendedSmartMeterOhItemNames) -> ExtendedSmartMeterValues:
        return ExtendedSmartMeterValues.create(self.get_item_value_list_from_items(oh_item_names))

    PersistenceValuesType = List[List[float]]
    def _get_persistence_values(self, oh_item_names : Tuple[str, ...], timedelta : datetime.timedelta) -> PersistenceValuesType:
        pers_values = []
        end_time=datetime.datetime.now()
        start_time=end_time-timedelta
        for item in oh_item_names:
            if item:
                values=[]
                try:
                    with self._session.get(
                        url=f"{self._oh_host}/rest/persistence/items/{item}", 
                        params={'starttime': start_time.isoformat(), 'endtime': end_time.isoformat()}) as response:
                        if response.status_code != http.HTTPStatus.OK:
                            self._logger.warning(f"Failed to get persistence values from openhab item {item}. Return code: {response.status_code}. text: {response.text})")
                        else:
                            values=[float(data['state']) for data in response.json()['data']]
                except requests.exceptions.RequestException as e:
                    self._logger.warning("Caught Exception while getting persistence data from openHAB: " + str(e))
                pers_values.append(values)
        return pers_values

    def check_if_updated(self, oh_item_names : Tuple[str, ...], timedelta : datetime.timedelta) -> bool:
        pers_values=self._get_persistence_values(oh_item_names, timedelta)
        for values in pers_values:
            if all(i == values[0] for i in values):
                return False
        return True

    def get_median_from_items(self, oh_item_names : SmartMeterOhItemNames, timedelta : datetime.timedelta = datetime.timedelta(minutes=30)) -> SmartMeterValues:
        smart_meter_values : List[OhItemAndValue] = []
        pers_values=self._get_persistence_values(oh_item_names, timedelta)
        value_index=0
        for item in oh_item_names:
            if item:
                avg_value = median(pers_values[value_index]) if len(pers_values[value_index]) > 10 else None
                smart_meter_values.append(OhItemAndValue(item, avg_value))
                value_index+=1
        return SmartMeterValues.create(smart_meter_values)

