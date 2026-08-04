from _service import get_device_data, get_filter_sensor_data, get_location_data


def query_device_info_by_id(
    device_id: int,
    sensor_type_filter: str = "",
    sensor_name_filter: str = "",
) -> dict:
    """
    Return device information, sensors, and current location data for a given device ID.

    If device_id is not found, return an empty dict.
    If sensors are not found, return an empty list for the "sensors" key.
    If location data is not found, return a dict with no location information.
    """
    device = get_device_data(device_id)
    if not device:
        return {}

    sensors = get_filter_sensor_data(device_id, sensor_type_filter, sensor_name_filter)

    location = get_location_data(device["deviceCode"])

    return device | {"sensors": sensors} | location
