import json
import os
import socket

import streamlit as st
from oncdw import ONCDW

# --- IMPORT ALL BACKEND LOGIC FROM HELPERS ---
from helpers import (
    PAGES_DIR,
    _apply_concurrent_scalar_prefetch,
    get_jira_instr_tickets,
    get_onc_annotations,
    render_custom_global_map,
)

# ==============================================================================
# --- TEMPLATES ---
# ==============================================================================

# 🛑 SOCKET GUARD: Instantly fail DNS resolution for Jira on Streamlit Cloud
if os.path.exists("/mount/src"):
    _orig_getaddrinfo = socket.getaddrinfo

    def _block_jira_dns(host, port, family=0, type=0, proto=0, flags=0):
        if host and "jira.oceannetworks.ca" in str(host):
            raise socket.gaierror(
                -2, "Jira DNS resolution blocked on Streamlit Cloud"
            )
        return _orig_getaddrinfo(host, port, family, type, proto, flags)

    socket.getaddrinfo = _block_jira_dns

# --- Template 1 --------------------------------------------------------------------------------------------------
def template1(
    json_filename: str,
    location_code: str,
    page_title: str,
    links: dict,
    env: str = "PROD",
    sticky_device: bool = False,
    sticky_location: bool = False,
):
    st.set_page_config(layout="wide", page_title=page_title)

    with open(PAGES_DIR / f"{json_filename}_1.json", encoding="utf-8") as f:
        devices1 = json.load(f)
    with open(PAGES_DIR / f"{json_filename}_2.json", encoding="utf-8") as f:
        devices2 = json.load(f)

    client = ONCDW(env=env)
    client.widget.map = render_custom_global_map
    _apply_concurrent_scalar_prefetch(client, [devices1, devices2], date_from="-P7D")
    st.title(f"{page_title} Monitoring Dashboard")
    client.ui.import_custom_badge_css(
        sticky_device=sticky_device, sticky_location=sticky_location
    )

    client.section.map(location_code, zoom=7)
    client.section.links(links)
    state_of_ocean_images_badges = client.section.state_of_ocean_images(location_code)

    with st.sidebar:
        client.ui.badge(2, "", "Links", "#links")
        for key, val, href in state_of_ocean_images_badges:
            client.ui.badge(2, key, val, href)
        st.divider()

        for device in devices1:
            client.section.location_sidebar(device)
            client.ui.device_sidebar(device)
            client.section.sensor_sidebar(device["sensors"])
            st.divider()
        for device in devices2:
            client.section.location_sidebar(device)
            client.ui.device_sidebar(device)
            st.divider()

    for device in devices1:
        client.section.location_expander(device)
        client.ui.device(device)
        st.subheader("Time Series plot")
        client.section.time_series(device["sensors"])

    for device in devices2:
        client.section.location_expander(device)
        client.ui.device(device)
        client.section.data_preview(device)
        if device.get("device_code", None) or device.get("deviceCode", None):
            st.subheader("Archive file table")
            client.widget.table_archive_files(device, date_from="-P4D")


# --- Template 2 --------------------------------------------------------------------------------------------------
def template2(
    json_filename: str,
    page_title: str,
    links: dict,
    center_lat: float | None = None,
    center_lon: float | None = None,
    zoom: int | None = 8,
    sticky_device: bool = False,
    sticky_location: bool = False,
):
    st.set_page_config(layout="wide", page_title=page_title)

    with open(PAGES_DIR / f"{json_filename}.json", encoding="utf-8") as f:
        devices = json.load(f)

    client = ONCDW()
    client.widget.map = render_custom_global_map
    _apply_concurrent_scalar_prefetch(client, [devices], date_from="-P7D")

    client.ui.import_custom_badge_css(
        sticky_device=sticky_device, sticky_location=sticky_location
    )
    st.title(f"{page_title} Monitoring Dashboard")

    with st.sidebar:
        client.ui.badge(2, "", "Links", "#links")
        st.divider()
        for device in devices:
            client.section.location_sidebar(device)
            client.ui.device_sidebar(device)
            client.section.sensor_sidebar(device.get("sensors", []))
            st.divider()

    client.widget.map(devices, center_lat=center_lat, center_lon=center_lon, zoom=zoom)
    client.section.links(links)

    for device in devices:
        client.section.location_expander(device)
        client.ui.device(device)
        client.section.data_preview(device)
        st.subheader("Time Series plot")
        client.section.time_series(device["sensors"])


# --- Template 3 --------------------------------------------------------------------------------------------------
def template3(
    json_filename: str,
    page_title: str,
    center_lat: float | None = None,
    center_lon: float | None = None,
    zoom: int | None = None,
    sticky_device: bool = False,
):
    st.set_page_config(layout="wide", page_title=page_title)

    with open(PAGES_DIR / f"{json_filename}.json", encoding="utf-8") as f:
        devices: dict = json.load(f)

    client = ONCDW(show_info=True)
    client.widget.map = render_custom_global_map

    _apply_concurrent_scalar_prefetch(client, [devices], date_from="-P7D")
    client.ui.import_custom_badge_css(sticky_device=sticky_device)

    st.title(f"{page_title} Monitoring Dashboard")

    if "lat" in devices[0] and "lon" in devices[0]:
        client.widget.map(
            devices, center_lat=center_lat, center_lon=center_lon, zoom=zoom
        )

    with st.sidebar:
        st.title("List of Devices")

        for device in devices:
            client.ui.location_sidebar(device)
            client.ui.device_sidebar(device)
            client.section.sensor_sidebar(device.get("sensors", []))
            st.divider()

    for device in devices:
        client.section.location_expander(device)
        client.ui.device(device)
        client.section.data_preview(device)

        st.subheader("List of last Archive Files for last 7 days")
        client.widget.table_archive_files(device, date_from="-P7D")

        if "sensors" in device and len(device["sensors"]):
            st.subheader("Time series for last 7 days")
            client.section.time_series(device["sensors"], date_from="-P7D")


# --- Template 4 --------------------------------------------------------------------------------------------------
def template4(
    json_filename: str,
    page_title: str,
    env: str = "PROD",
    sticky_device: bool = False,
    sticky_location: bool = False,
):
    st.set_page_config(layout="wide", page_title=page_title)

    with open(PAGES_DIR / f"{json_filename}.json", encoding="utf-8") as f:
        devices2 = json.load(f)

    client = ONCDW(env=env)
    client.widget.map = render_custom_global_map
    _apply_concurrent_scalar_prefetch(client, [devices2], date_from="-P7D")

    st.title(f"{page_title} Monitoring Dashboard")
    client.ui.import_custom_badge_css(
        sticky_device=sticky_device, sticky_location=sticky_location
    )

    with st.sidebar:
        st.title("List of Devices")
        for device in devices2:
            client.ui.location_sidebar(device)
            client.ui.device_sidebar(device)
            st.divider()

    for device in devices2:
        client.section.location_expander(device)
        client.ui.device(device)
        st.divider()
        client.section.data_preview(device)


# --- Template 3b (With Debugging Instrumentation) ------------------------------------------------------------------
def template3b(
    json_filename: str,
    page_title: str,
    center_lat: float | None = None,
    center_lon: float | None = None,
    zoom: int | None = None,
):
    st.set_page_config(layout="wide", page_title=page_title)

    # --------------------------------------------------------------------------
    # Environment Check: Streamlit Cloud uses '/mount/src'
    # --------------------------------------------------------------------------
    is_local_env = not os.path.exists("/mount/src")

    st.caption(
        f"🔍 **Debug Mode Active** | Environment: **{'Local Machine' if is_local_env else 'Streamlit Cloud'}**"
    )

    # 1. Load JSON Data
    try:
        with open(PAGES_DIR / f"{json_filename}.json", encoding="utf-8") as f:
            devices: list = json.load(f)
    except Exception as e:
        st.error(f"❌ Failed to load JSON file ({json_filename}.json): {e}")
        return

    primary_location = {
        "locationCode": devices[0].get(
            "locationCode", devices[0].get("location_code")
        ),
        "locationName": devices[0].get(
            "locationName", devices[0].get("location_name")
        ),
        "lat": devices[0].get("lat"),
        "lon": devices[0].get("lon"),
    }

    for device in devices:
        if "locationCode" not in device and "location_code" not in device:
            device["locationCode"] = primary_location["locationCode"]
            device["locationName"] = primary_location["locationName"]
            device["lat"] = primary_location["lat"]
            device["lon"] = primary_location["lon"]

    # 2. Initialize ONCDW Client
    try:
        client = ONCDW(show_info=True)
        client.widget.map = render_custom_global_map
    except Exception as e:
        st.error(f"❌ ONCDW Client Initialization Failed: {e}")

    # 3. Scalar Prefetch Check
    try:
        with st.spinner("🔄 Prefetching scalar data..."):
            _apply_concurrent_scalar_prefetch(
                client, [devices], date_from="-P7D"
            )
    except Exception as e:
        st.warning(f"⚠️ Concurrent scalar prefetch failed or timed out: {e}")

    all_dev_ids = tuple(
        int(d.get("deviceId", d.get("device_id")))
        for d in devices
        if d.get("deviceId", d.get("device_id"))
    )

    # 4. Jira & Annotations
    jira_instr_data = (
        get_jira_instr_tickets(all_dev_ids) if is_local_env else {}
    )
    annotation_data = (
        get_onc_annotations(all_dev_ids) if is_local_env else {}
    )

    try:
        client.ui.import_custom_badge_css(sticky_device=False)
    except Exception as e:
        st.warning(f"⚠️ Badge CSS import failed: {e}")

    st.title(f"{page_title} Monitoring Dashboard")

    # 5. Map Rendering Check
    if devices and "lat" in devices[0] and "lon" in devices[0]:
        try:
            client.widget.map(
                devices, center_lat=center_lat, center_lon=center_lon, zoom=zoom
            )
        except Exception as e:
            st.error(f"❌ Map rendering failed: {e}")

    st.divider()

    st.subheader("State of the Ocean Environment")
    loc_code = primary_location["locationCode"]

    left_spacer, center_col, right_spacer = st.columns([1, 3.5, 1])
    with center_col:
        try:
            st.caption("Climate")
            st.image(
                f"https://ftp.oceannetworks.ca/pub/DataProducts/SOO/{loc_code}/{loc_code}-StateOfOceanEnv-Climate.png",
                width="stretch",
            )
            st.caption("Anomaly")
            st.image(
                f"https://ftp.oceannetworks.ca/pub/DataProducts/SOO/{loc_code}/{loc_code}-StateOfOceanEnv-Anomaly.png",
                width="stretch",
            )
            st.caption("Min / Max / Avg (1-Day)")
            st.image(
                f"https://ftp.oceannetworks.ca/pub/DataProducts/SOO/{loc_code}/{loc_code}-StateOfOceanEnv_MinMaxAvg1day.png",
                width="stretch",
            )
        except Exception as e:
            st.warning(f"⚠️ State of the Ocean images failed to load: {e}")

    st.divider()

    # 6. Sidebar Rendering Check
    with st.sidebar:
        st.title("List of Devices")
        for device in devices:
            try:
                client.ui.location_sidebar(device)
                client.ui.device_sidebar(device)
                client.section.sensor_sidebar(device.get("sensors", []))
            except Exception as e:
                st.error(f"❌ Sidebar device rendering failed: {e}")
            st.divider()

    # 7. Device Loop Checks
    for device in devices:
        st.divider()
        try:
            client.section.location_expander(device)
        except Exception as e:
            st.warning(f"⚠️ Location expander failed: {e}")

        dev_id = device.get("deviceId", device.get("device_id", "Unknown ID"))
        dev_name = device.get(
            "deviceName", device.get("device_name", "Unknown Device")
        )

        st.subheader(f"{dev_name} ({dev_id})")

        try:
            client.ui.device(device)
        except Exception as e:
            st.error(f"❌ Device UI block failed for {dev_name}: {e}")

        # --- JIRA TICKETS SECTION ---
        if not is_local_env:
            st.caption(
                "🎫 *Jira tickets are only accessible on the internal ONC network.*"
            )
        else:
            tickets = jira_instr_data.get(int(dev_id), [])
            if tickets:
                with st.expander(
                    f"🎫 **Active Jira Tickets ({len(tickets)})**",
                    expanded=True,
                ):
                    for t in tickets:
                        st.markdown(
                            f"- **[{t['key']}]({t['link']})** | *{t['status']}* | {t['summary']}"
                        )
            else:
                st.caption("🎫 *No active Jira tickets.*")

        # --- ANNOTATIONS SECTION ---
        if not is_local_env:
            st.caption(
                "📝 *Annotations are only accessible on the internal ONC network.*"
            )
        else:
            annotations = annotation_data.get(int(dev_id), [])
            if annotations:
                with st.expander(
                    f"📝 **Active Annotations ({len(annotations)})**",
                    expanded=True,
                ):
                    for a in annotations:
                        st.markdown(f"- **{a['date']}** | {a['text']}")
            else:
                st.caption("📝 *No active annotations.*")

        st.write("")

        # --- ARCHIVE FILES TABLE CHECK ---
        dev_code = device.get("deviceCode", device.get("device_code"))
        if dev_code:
            with st.expander(
                "📦 **Archive Files (Last 3 Days)**", expanded=True
            ):
                try:
                    client.widget.table_archive_files(device, date_from="-P3D")
                except Exception as e:
                    st.error(
                        f"❌ Archive Files Table failed for {dev_code}: {e}"
                    )
            st.write("")

        # --- TIME SERIES PLOTS CHECK ---
        sensors_list = device.get("sensors", [])
        if sensors_list:
            try:
                client.section.time_series(sensors_list, date_from="-P7D")
            except Exception as e:
                st.error(
                    f"❌ Time Series plots failed for device {dev_id}: {e}"
                )

    # 8. CTD vs Oxygen Temp Comparison Check
    ctd_temp = None
    oxy_temp = None

    for device in devices:
        device_name = device.get("deviceName", device.get("device_name", ""))
        device_category = device.get(
            "deviceCategory", device.get("device_category", "")
        )
        sensors_list = device.get("sensors", [])

        is_ctd = (
            "CTD" in device_name.upper()
            or "CONDUCTIVITY" in device_category.upper()
        )
        is_oxy = (
            "OXYGEN" in device_name.upper()
            or "OXYGEN" in device_category.upper()
        )

        if is_ctd or is_oxy:
            for sensor in sensors_list:
                s_name = sensor.get(
                    "sensorName", sensor.get("sensor_name", "")
                )
                s_type = sensor.get(
                    "sensorType", sensor.get("sensor_type", "")
                )
                s_id = sensor.get("sensorId", sensor.get("sensor_id"))

                if (
                    "TEMPERATURE" in s_name.upper()
                    or "TEMPERATURE" in s_type.upper()
                ):
                    simple_device_name = "CTD" if is_ctd else "Oxygen"
                    sensor_info = {
                        "sensorId": s_id,
                        "sensorName": f"{simple_device_name} ({s_name})",
                    }

                    if is_ctd and not ctd_temp:
                        ctd_temp = sensor_info
                    elif is_oxy and not oxy_temp:
                        oxy_temp = sensor_info

    if ctd_temp and oxy_temp:
        st.divider()
        st.subheader("Temperature Comparison: CTD vs. Oxygen Sensor")

        ctd_label = ctd_temp.get(
            "label",
            ctd_temp.get("sensorName", ctd_temp.get("sensor_name", "CTD")),
        )
        oxy_label = oxy_temp.get(
            "label",
            oxy_temp.get("sensorName", oxy_temp.get("sensor_name", "Oxygen")),
        )
        ctd_id = ctd_temp.get(
            "id", ctd_temp.get("sensorId", ctd_temp.get("sensor_id"))
        )
        oxy_id = oxy_temp.get(
            "id", oxy_temp.get("sensorId", oxy_temp.get("sensor_id"))
        )

        st.caption(f"Comparing: **{ctd_label}** vs. **{oxy_label}**")

        TIME_RANGE_MAP = {
            "24H": "-P1D",
            "7D": "-P7D",
            "2W": "-P14D",
            "1M": "-P30D",
        }
        selected_range = st.segmented_control(
            "Select Range",
            options=list(TIME_RANGE_MAP.keys()),
            default="7D",
            key=f"range_pair_ctd_oxy_{ctd_id}",
            label_visibility="collapsed",
        )

        if not selected_range:
            selected_range = "7D"

        try:
            client.widget.time_series_two_sensors(
                ctd_id,
                oxy_id,
                date_from=TIME_RANGE_MAP[selected_range],
                label1=ctd_label,
                label2=oxy_label,
                color1="royalblue",
                color2="red",
                shade=False,
            )
        except Exception as e:
            st.error(f"❌ Two-Sensor Comparison Plot failed: {e}")

            
# --- Template Coastal Observatories -------------------------------------------------------------------------------------------------
def template_coastal_obs(
    json_filename: str,
    page_title: str,
    center_lat: float | None = None,
    center_lon: float | None = None,
    zoom: int | None = None,
    SOO_plot: bool = True,
):
    st.set_page_config(layout="wide", page_title=page_title)

    # --------------------------------------------------------------------------
    # Environment Check: Streamlit Cloud uses '/mount/src'
    # --------------------------------------------------------------------------
    is_local_env = not os.path.exists("/mount/src")

    with open(PAGES_DIR / f"{json_filename}.json", encoding="utf-8") as f:
        devices: list = json.load(f)

    primary_location = {
        "locationCode": devices[0].get(
            "locationCode", devices[0].get("location_code")
        ),
        "locationName": devices[0].get(
            "locationName", devices[0].get("location_name")
        ),
        "lat": devices[0].get("lat"),
        "lon": devices[0].get("lon"),
    }

    for device in devices:
        if "locationCode" not in device and "location_code" not in device:
            device["locationCode"] = primary_location["locationCode"]
            device["locationName"] = primary_location["locationName"]
            device["lat"] = primary_location["lat"]
            device["lon"] = primary_location["lon"]

    client = ONCDW(show_info=True)
    client.widget.map = render_custom_global_map
    _apply_concurrent_scalar_prefetch(client, [devices], date_from="-P7D")

    all_dev_ids = tuple(
        int(d.get("deviceId", d.get("device_id")))
        for d in devices
        if d.get("deviceId", d.get("device_id"))
    )

    # 🌐 Only fetch Jira tickets & DB annotations if running locally
    jira_instr_data = (
        get_jira_instr_tickets(all_dev_ids) if is_local_env else {}
    )
    annotation_data = (
        get_onc_annotations(all_dev_ids) if is_local_env else {}
    )

    client.ui.import_custom_badge_css(sticky_device=False)
    st.title(f"{page_title} Monitoring Dashboard")

    if devices and "lat" in devices[0] and "lon" in devices[0]:
        client.widget.map(
            devices, center_lat=center_lat, center_lon=center_lon, zoom=zoom
        )

    st.divider()
    st.subheader("State of the Ocean Environment")
    loc_code = primary_location["locationCode"]

    if SOO_plot:
        left_spacer, center_col, right_spacer = st.columns([1, 3.5, 1])
        with center_col:
            st.caption("Climate")
            st.image(
                f"https://ftp.oceannetworks.ca/pub/DataProducts/SOO/{loc_code}/{loc_code}-StateOfOceanEnv-Climate.png",
                width="stretch",
            )
            st.caption("Anomaly")
            st.image(
                f"https://ftp.oceannetworks.ca/pub/DataProducts/SOO/{loc_code}/{loc_code}-StateOfOceanEnv-Anomaly.png",
                width="stretch",
            )
            st.caption("Min / Max / Avg (1-Day)")
            st.image(
                f"https://ftp.oceannetworks.ca/pub/DataProducts/SOO/{loc_code}/{loc_code}-StateOfOceanEnv_MinMaxAvg1day.png",
                width="stretch",
            )
        st.divider()

    with st.sidebar:
        st.title("List of Devices")
        for device in devices:
            client.ui.location_sidebar(device)
            client.ui.device_sidebar(device)
            client.section.sensor_sidebar(device.get("sensors", []))
            st.divider()

    for device in devices:
        st.divider()
        client.section.location_expander(device)
        dev_id = device.get("deviceId", device.get("device_id", "Unknown ID"))
        dev_name = device.get(
            "deviceName", device.get("device_name", "Unknown Device")
        )

        st.subheader(f"{dev_name} ({dev_id})")
        client.ui.device(device)

        # --- JIRA TICKETS SECTION ---
        if not is_local_env:
            st.caption(
                "🎫 *Jira tickets are only accessible on the internal ONC network.*"
            )
        else:
            tickets = jira_instr_data.get(int(dev_id), [])
            if tickets:
                with st.expander(
                    f"🎫 **Active Jira Tickets ({len(tickets)})**",
                    expanded=True,
                ):
                    for t in tickets:
                        st.markdown(
                            f"- **[{t['key']}]({t['link']})** | *{t['status']}* | {t['summary']}"
                        )
            else:
                st.caption("🎫 *No active Jira tickets.*")

        # --- ANNOTATIONS SECTION ---
        if not is_local_env:
            st.caption(
                "📝 *Annotations are only accessible on the internal ONC network.*"
            )
        else:
            annotations = annotation_data.get(int(dev_id), [])
            if annotations:
                with st.expander(
                    f"📝 **Active Annotations ({len(annotations)})**",
                    expanded=True,
                ):
                    for a in annotations:
                        st.markdown(f"- **{a['date']}** | {a['text']}")
            else:
                st.caption("📝 *No active annotations.*")

        st.write("")
        sensors_list = device.get("sensors", [])
        if sensors_list:
            client.section.time_series(sensors_list, date_from="-P7D")

    ctd_temp = None
    oxy_temp = None

    for device in devices:
        device_name = device.get("deviceName", device.get("device_name", ""))
        device_category = device.get(
            "deviceCategory", device.get("device_category", "")
        )
        sensors_list = device.get("sensors", [])

        is_ctd = (
            "CTD" in device_name.upper()
            or "CONDUCTIVITY" in device_category.upper()
        )
        is_oxy = (
            "OXYGEN" in device_name.upper()
            or "OXYGEN" in device_category.upper()
        )

        if is_ctd or is_oxy:
            for sensor in sensors_list:
                s_name = sensor.get(
                    "sensorName", sensor.get("sensor_name", "")
                )
                s_type = sensor.get(
                    "sensorType", sensor.get("sensor_type", "")
                )
                s_id = sensor.get("sensorId", sensor.get("sensor_id"))

                if (
                    "TEMPERATURE" in s_name.upper()
                    or "TEMPERATURE" in s_type.upper()
                ):
                    simple_device_name = "CTD" if is_ctd else "Oxygen"
                    sensor_info = {
                        "sensorId": s_id,
                        "sensorName": f"{simple_device_name} ({s_name})",
                    }

                    if is_ctd and not ctd_temp:
                        ctd_temp = sensor_info
                    elif is_oxy and not oxy_temp:
                        oxy_temp = sensor_info

    if ctd_temp and oxy_temp:
        st.divider()
        st.subheader("Temperature Comparison: CTD vs. Oxygen Sensor")

        # Safely extract labels and IDs whether the key is 'label', 'sensorName', etc.
        ctd_label = ctd_temp.get(
            "label",
            ctd_temp.get("sensorName", ctd_temp.get("sensor_name", "CTD")),
        )
        oxy_label = oxy_temp.get(
            "label",
            oxy_temp.get("sensorName", oxy_temp.get("sensor_name", "Oxygen")),
        )
        ctd_id = ctd_temp.get(
            "id", ctd_temp.get("sensorId", ctd_temp.get("sensor_id"))
        )
        oxy_id = oxy_temp.get(
            "id", oxy_temp.get("sensorId", oxy_temp.get("sensor_id"))
        )

        st.caption(f"Comparing: **{ctd_label}** vs. **{oxy_label}**")

        TIME_RANGE_MAP = {
            "24H": "-P1D",
            "7D": "-P7D",
            "2W": "-P14D",
            "1M": "-P30D",
        }
        selected_range = st.segmented_control(
            "Select Range",
            options=list(TIME_RANGE_MAP.keys()),
            default="7D",
            key=f"range_pair_ctd_oxy_{ctd_id}",
            label_visibility="collapsed",
        )

        if not selected_range:
            selected_range = "7D"

        client.widget.time_series_two_sensors(
            ctd_id,
            oxy_id,
            date_from=TIME_RANGE_MAP[selected_range],
            label1=ctd_label,
            label2=oxy_label,
            color1="royalblue",
            color2="red",
            shade=False,
        )