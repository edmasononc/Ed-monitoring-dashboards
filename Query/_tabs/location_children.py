import streamlit as st
from _service import get_device_id_from_location_children


def location_children_tab():
    location_code = st.text_input(
        "Enter a location code:", key="location_code", value="NEP"
    )
    device_category_code = st.text_input(
        "Enter a device category code:", key="device_category_code", value="BPR"
    )

    if st.button("Query Location Children"):
        device_ids = get_device_id_from_location_children(
            location_code, device_category_code
        )
        st.write("Output can be directly used (copy + paste) in Device Info tab.")
        st.json(device_ids)
