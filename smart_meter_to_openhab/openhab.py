import requests
import http
import datetime
from logging import Logger
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter, Retry
from typing import List
from statistics import median
from .interfaces import SmartMeterValues, OhItemAndValue, create_smart_meter_values

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

    def post_to_items(self, values : SmartMeterValues) -> None:
        for v in values.convert_to_item_value_list():
            if v.value is not None:
                try:
                    with self._session.post(url=f"{self._oh_host}/rest/items/{v.oh_item}", data=str(v.value)) as response:
                        if response.status_code != http.HTTPStatus.OK:
                            self._logger.warning(f"Failed to post value to openhab item {v.oh_item}. Return code: {response.status_code}. text: {response.text})")
                except requests.exceptions.RequestException as e:
                    self._logger.warning("Caught Exception: " + str(e))

    def get_from_items(self, oh_items : List[str]) -> SmartMeterValues:
        values : List[OhItemAndValue] = []
        for item in oh_items:
            try:
                with self._session.get(url=f"{self._oh_host}/rest/items/{item}/state") as response:
                    if response.status_code != http.HTTPStatus.OK:
                        self._logger.warning(f"Failed to get value from openhab item {item}. Return code: {response.status_code}. text: {response.text})")
                    else:
                        values.append(OhItemAndValue(item, response.text.split()[0]))
            except requests.exceptions.RequestException as e:
                values.append(OhItemAndValue(item))
                self._logger.warning("Caught Exception: " + str(e))
        return create_smart_meter_values(values)

    def get_median_from_items(self, oh_items : List[str], timedelta : datetime.timedelta = datetime.timedelta(minutes=30)) -> SmartMeterValues:
        smart_meter_values : List[OhItemAndValue] = []
        end_time=datetime.datetime.now()
        start_time=end_time-timedelta
        for item in oh_items:
            try:   
                with self._session.get(
                    url=f"{self._oh_host}/rest/persistence/items/{item}", 
                    params={'starttime': start_time.isoformat(), 'endtime': end_time.isoformat()}) as response:
                    if response.status_code != http.HTTPStatus.OK:
                        self._logger.warning(f"Failed to get average value from openhab item {item}. Return code: {response.status_code}. text: {response.text})")
                    else:
                        item_values = [float(data['state']) for data in response.json()['data']]
                        avg_value = median(item_values) if len(item_values) > 10 else None
                        smart_meter_values.append(OhItemAndValue(item, avg_value))
            except requests.exceptions.RequestException as e:
                self._logger.warning("Caught Exception: " + str(e))
                smart_meter_values.append(OhItemAndValue(item))
        return create_smart_meter_values(smart_meter_values)

