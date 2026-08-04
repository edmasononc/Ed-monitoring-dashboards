import streamlit as st
from _query import query_device_info_by_id
from _util import add_data_preview_options


def _handle_device_info_exception(device: dict, device_id: int):
    if not device:
        st.error(f"Device not found for id {device_id}.")
    else:
        if not device["sensors"]:
            st.warning(f"Sensors not found for device id {device_id}.")

        if "locationCode" not in device:
            st.warning(f"Location not found for device id {device_id}.")
        elif not device.get("searchTreeNodeId", ""):
            st.warning(
                f"searchTreeNodeId not found for device id {device_id} and locationCode {device['locationCode']}."
            )


def device_id_tab():
    device_ids = st.text_area(
        "Enter a device ID or multiple IDs separated by comma, optionally in brackets: (e.g., 1; [2,3]; 4, 5, 6)",
        key="device_id",
        value="[23283,67660]",
    )
    col1, col2 = st.columns(2)
    with col1:
        sensor_filters = st.toggle("Enable sensor filters")
    with col2:
        data_preview_options = st.toggle("Add data preview options")

    if sensor_filters:
        sensor_name_filter = st.text_input(
            "Sensor name filter (use comma separated texts for or filters):",
            key="sensor_name_filter",
            placeholder="temp, oxygen",
        )

        sensor_type_filter = st.text_input(
            "Sensor type filter (use comma separated texts for or filters):",
            key="sensor_type_filter",
        )
    else:
        sensor_name_filter = ""
        sensor_type_filter = ""

    if data_preview_options:
        data_product_ids = st.text_input("data_product_format_id (separated by comma)")
        plot_number = st.number_input(
            "plot number", min_value=1, max_value=1000, value=1
        )

    st.divider()

    if st.button("Query Device Info"):
        if not device_ids:
            st.warning("Please enter device ID(s).")
            st.stop()

        device_id_list = [
            int(device_id.strip()) for device_id in device_ids.strip("[]").split(",")
        ]

        all_device_info = []
        for device_id in device_id_list:
            device = query_device_info_by_id(
                device_id,
                sensor_type_filter=sensor_type_filter,
                sensor_name_filter=sensor_name_filter,
            )
            _handle_device_info_exception(device, device_id)
            if device:
                if data_preview_options:
                    device = add_data_preview_options(
                        device, data_product_ids, plot_number
                    )
                all_device_info.append(device)
        st.json(all_device_info)
