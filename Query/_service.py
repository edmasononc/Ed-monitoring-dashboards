import os
import re  # Added for matching non-descriptive legacy tags cleanly

import requests
import streamlit as st
from _util import filter_dict
from onc import ONC


@st.cache_data(ttl=300)
def get_device_data(device_id: int) -> dict:
    """
    Fetches general device info. Falls back directly to the ONC database API
    if the portal scraping endpoint returns empty due to missing active sensors.
    """
    device_url = f"https://data.oceannetworks.ca/DeviceGeneralTabService?operation=1&deviceId={device_id}"
    try:
        response = requests.get(device_url)
        device = response.json().get("payload", {})
    except Exception:
        device = {}

    # FALLBACK LAYER: If portal scrape is empty, query the database API directly
    if not device:
        try:
            onc = ONC(os.getenv("ONC_TOKEN"))
            api_res = onc.getDevices({"deviceId": device_id})
            if api_res:
                device = api_res[0]
                # Normalize category naming conventions between API and Portal structures
                if "deviceCategory" not in device and "deviceCategoryName" in device:
                    device["deviceCategory"] = device["deviceCategoryName"]
        except Exception:
            return {}

    if not device:
        return {}

    device["deviceId"] = device_id
    filter_device_keys = [
        "deviceId",
        "deviceName",
        "deviceCode",
        "deviceCategory",
        "deviceCategoryId",
    ]

    return filter_dict(device, filter_device_keys)


def _can_text_match_filter(text: str, filter: str) -> bool:
    if not filter:
        return True
    filters = [s_type.strip().lower() for s_type in filter.split(",")]
    return any(s_type in text.lower() for s_type in filters)


def _filter_sensor(
    sensor: dict, sensor_type_filter: str, sensor_name_filter: str
) -> bool:
    """
    Return if the sensor matches the type and name filters.
    """
    return _can_text_match_filter(
        sensor["sensorType"], sensor_type_filter
    ) and _can_text_match_filter(sensor["sensorName"], sensor_name_filter)


@st.cache_data(ttl=300)
def get_sensor_data(device_id: int) -> list:
    """
    Return a list of sensors for a given device ID, filtered by sensor type and name.
    If no sensors are found, return an empty list.
    """
    sensor_url = (
        f"https://data.oceannetworks.ca/DeviceSensorService?deviceId={device_id}"
    )
    response = requests.get(sensor_url)

    filter_sensor_keys = [
        "sensorId",
        "sensorName",
        "sensorType",
        "sensorCode",
        "sensorCodeId",
    ]

    sensors = response.json().get("payload", [])

    if not sensors:
        return []
        
    res = []
    for sensor in sensors:
        sensor["sensorCodeId"] = st.session_state["sensor_code"].get(
            sensor["sensorCode"]
        )
        res.append(filter_dict(sensor, filter_sensor_keys))
        
    # ==========================================================================
    # --- SENSOR FILTERING & ALPHABETICAL SORTING LAYER ---
    # ==========================================================================
    
    # 1. Drop non-descriptive legacy VX sensors (e.g., V0, V1, V2 ... V5)
    res = [
        sensor for sensor in res 
        if not re.match(r"^V\d+$", str(sensor.get("sensorName", "")))
    ]
    
    # 2. Sort remaining sensors alphabetically by sensorName (case-insensitive)
    res.sort(key=lambda x: str(x.get("sensorName", "")).lower())
    
    return res


def get_filter_sensor_data(
    device_id: int, sensor_type_filter: str, sensor_name_filter: str
) -> list:
    """
    Filter sensors by sensor type and name, and only keep relevant keys.
    """
    sensors = get_sensor_data(device_id)
    return list(
        filter(
            lambda sensor: _filter_sensor(
                sensor, sensor_type_filter, sensor_name_filter
            ),
            sensors,
        )
    )


@st.cache_data(ttl=300)
def get_device_id_from_location_children(
    location_code: str, device_category_code: str
) -> list:
    """
    Return a list of device IDs for a given location code and device category code.
    If no devices are found, return an empty list.
    """
    onc = ONC(os.getenv("ONC_TOKEN"))
    device_ids = []
    try:
        locations_children = onc.getLocations(
            {
                "deviceCategoryCode": device_category_code,
                "locationCode": location_code,
                "dateFrom": "-P1D",
                "includeChildren": True,
            }
        )

        for loc_child in locations_children:
            devices = onc.getDevices(
                {
                    "locationCode": loc_child["locationCode"],
                    "deviceCategoryCode": device_category_code,
                    "dateFrom": "-P1D",
                }
            )
            device_ids.append(devices[0]["deviceId"])  # current device

    except Exception:
        return []

    return device_ids


@st.cache_data(ttl=300)
def get_location_data(device_code: str) -> dict:
    """
    Return the current location data for a given device code.
    Removes time constraints if a device has no active current deployments.
    """
    onc = ONC(os.getenv("ONC_TOKEN"))

    try:
        # First try to find active current deployments within the last 24 hours
        locations = onc.getLocations({"deviceCode": device_code, "dateFrom": "-P1D"})
        
        # Fallback: remove date restriction to fetch the asset's historical assignment details
        if not locations:
            locations = onc.getLocations({"deviceCode": device_code})
            
        if not locations:
            return {}
            
        location = locations[0]
        location["searchTreeNodeId"] = st.session_state["search_tree_node"].get(
            location.get("locationCode"), ""
        )

        filter_location_keys = [
            "locationName",
            "locationCode",
            "searchTreeNodeId",
            "lat",
            "lon",
        ]
        return filter_dict(location, filter_location_keys)
    except Exception:
        return {}


def get_search_tree_node_code_id_dict_from_database() -> dict:
    conn = st.connection("postgresql", type="sql")
    df = conn.query(
        "SELECT searchtreenodecode, searchtreenodeid FROM searchtreenode order by searchtreenodeid;"
    )
    return df.set_index("searchtreenodecode")["searchtreenodeid"].to_dict()


def get_sensor_code_id_dict_from_database() -> dict:
    conn = st.connection("postgresql", type="sql")
    df = conn.query(
        "SELECT sensorcodeid, sensorcode FROM sensorcode order by sensorcodeid;"
    )
    return df.set_index("sensorcode")["sensorcodeid"].to_dict()