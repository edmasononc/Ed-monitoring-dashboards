import json
from pathlib import Path

import streamlit as st
from _service import get_sensor_code_id_dict_from_database

from _tabs._json_update_helpers import build_json_diff, read_json_file

SENSOR_CODE_JSON_PATH = Path("./Query/sensor_code.json")
SENSOR_CODE_PENDING_KEY = "pending_sensor_code_update"
SENSOR_CODE_DIFF_KEY = "pending_sensor_code_diff"


@st.dialog("Update sensorCode")
def update_sensor_code_dialog():
    st.text("This will query the PROD database to update the sensorCode json file.")
    st.markdown(
        "Make sure you are on the dev server in the local internet or connected to the VPN, not on the :red[**Streamlit Community Cloud**]."
    )
    st.text(
        "You need to restart the app to apply changes. Also you probably want to push the changes to GitHub after updating."
    )
    st.text("Click the x icon to cancel.")

    if st.button("Proceed?", type="primary", key="sensor_code_proceed"):
        try:
            updated_sensor_code = get_sensor_code_id_dict_from_database()
            st.success("Retrieved sensorCode from database successfully.")

            current_sensor_code = read_json_file(SENSOR_CODE_JSON_PATH)
            diff_text = build_json_diff(
                current_sensor_code,
                updated_sensor_code,
                file_name="sensor_code.json",
            )

            if not diff_text:
                st.info("No changes detected. sensor_code.json was not modified.")
                st.session_state.pop(SENSOR_CODE_PENDING_KEY, None)
                st.session_state.pop(SENSOR_CODE_DIFF_KEY, None)
            else:
                st.session_state[SENSOR_CODE_PENDING_KEY] = updated_sensor_code
                st.session_state[SENSOR_CODE_DIFF_KEY] = diff_text
                st.warning("Differences found. Review and accept to apply changes.")
        except Exception as e:
            st.error(f"Error retrieving sensorCode dictionary: {e}")

    pending_update = st.session_state.get(SENSOR_CODE_PENDING_KEY)
    diff_text = st.session_state.get(SENSOR_CODE_DIFF_KEY)
    if pending_update and diff_text:
        st.markdown("### Proposed changes")
        st.code(diff_text, language="diff")
        accept_col, reject_col = st.columns(2)

        with accept_col:
            if st.button("Accept changes", type="primary", key="sensor_code_accept"):
                with SENSOR_CODE_JSON_PATH.open("w") as f:
                    json.dump(pending_update, f, indent=4)
                st.success("Updated sensor_code.json successfully.")
                st.session_state.pop(SENSOR_CODE_PENDING_KEY, None)
                st.session_state.pop(SENSOR_CODE_DIFF_KEY, None)

        with reject_col:
            if st.button("Reject changes", key="sensor_code_reject"):
                st.session_state.pop(SENSOR_CODE_PENDING_KEY, None)
                st.session_state.pop(SENSOR_CODE_DIFF_KEY, None)
                st.info("Changes discarded.")


def sensor_code_tab():
    if st.button("Update sensorCode dictionary", type="primary"):
        update_sensor_code_dialog()

    sensor_code = st.text_input("Query sensorCodeId by sensor code:")

    if st.button("Get sensorCodeId"):
        if sensor_code:
            sensor_code_id = st.session_state["sensor_code"].get(sensor_code)
            if sensor_code_id:
                st.success(
                    f"sensorCodeId for sensor code '{sensor_code}': {sensor_code_id}"
                )
            else:
                st.error(f"Sensor code '{sensor_code}' not found in the dictionary.")
        else:
            st.warning("Please enter a sensor code.")
