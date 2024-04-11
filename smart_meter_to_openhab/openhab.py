import requests
import http
import datetime
from logging import Logger
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter, Retry
from typing import List, Tuple
from statistics import median
from .interfaces import *

# disable warnings about insecure requests because ssl verification is disabled
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def _convert_list_to_smart_meter_values(oh_item_names : SmartMeterOhItemNames, 
                                       list_values : List[List[float]]) -> List[SmartMeterValues]:
    smart_meter_values : List[SmartMeterValues] = []
    valid_items=[item for item in oh_item_names if item]
    for value_index in range(len(list_values[0]) if list_values else 0):
        item_value_list : List[OhItemAndValue] = []
        for item_index, item in enumerate(valid_items):
            item_value_list.append(OhItemAndValue(item, list_values[item_index][value_index]))
        smart_meter_values.append(SmartMeterValues.create(item_value_list))
    return smart_meter_values

def _check_if_updated(values : List[SmartMeterValues]) -> bool:
    valid_values : List[SmartMeterValues] = [value for value in values if value.is_valid()]
    if len(valid_values) < 2:
        return False

    # no consumption is good and considered as updated
    if all((value.overall_consumption.value is not None and value.overall_consumption.value == 0) for value in valid_values):
        return True
    
    # for all other cases, at least one value has to be different
    if any(value != valid_values[0] for value in valid_values):
        return True
    
    return False

def _get_median(oh_item_names : SmartMeterOhItemNames, list_values : List[List[float]]) -> SmartMeterValues:
    smart_meter_values : List[OhItemAndValue] = []
    value_index=0
    for item in oh_item_names:
        if item:
            avg_value = median(list_values[value_index]) if len(list_values[value_index]) > 1 else None
            smart_meter_values.append(OhItemAndValue(item, avg_value))
            value_index+=1
    return SmartMeterValues.create(smart_meter_values)

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
                try:
                    with self._session.get(url=f"{self._oh_host}/rest/items/{item}/state", verify=False) as response:
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

    def check_if_persistence_values_updated(self, oh_item_names : SmartMeterOhItemNames, start_time : datetime.datetime, end_time : datetime.datetime) -> bool:
        pers_values=self._get_persistence_values(oh_item_names, start_time, end_time)
        if pers_values and any(len(values) != len(pers_values[0]) for values in pers_values):
            # return True in case the input lists are of unequal size
            # NOTE: This happens if the GET/POST requests to Openhab have not been completely successful.
            self._logger.warning("Persistence values are of unequal size. Assuming they have been updated.")
            return True
        
        smart_meter_values=_convert_list_to_smart_meter_values(oh_item_names, pers_values)
        return _check_if_updated(smart_meter_values)

    def get_median_from_items(self, oh_item_names : SmartMeterOhItemNames, 
                              timedelta : datetime.timedelta = datetime.timedelta(minutes=30)) -> SmartMeterValues:
        end_time=datetime.datetime.now()
        start_time=end_time-timedelta
        pers_values=self._get_persistence_values(oh_item_names, start_time, end_time)
        return _get_median(oh_item_names, pers_values)