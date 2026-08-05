import json
import os
import socket
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st
from jira import JIRA
from oncdw import ONCDW
from oncdw._util import parse_datetime_parameters

PAGES_DIR = Path(__file__).resolve().parent / "pages"


# 🛑 SOCKET GUARD: Instantly fail DNS resolution for Jira on Streamlit Cloud
if os.path.exists("/mount/src"):
    _orig_getaddrinfo = socket.getaddrinfo

    def _block_jira_dns(host, port, family=0, type=0, proto=0, flags=0):
        if host and "jira.oceannetworks.ca" in str(host):
            raise socket.gaierror(-2, "Jira DNS resolution blocked on Streamlit Cloud")
        return _orig_getaddrinfo(host, port, family, type, proto, flags)

    socket.getaddrinfo = _block_jira_dns


# ==============================================================================
# --- DYNAMIC GLOBAL PYDECK MAP ENGINE ---
# ==============================================================================
def render_custom_global_map(
    current_devices: list,
    center_lat: float | None = None,
    center_lon: float | None = None,
    zoom: int | None = None,
):
    """
    Scans all JSON files with safe row-level isolation. Plots background deployment
    nodes as soft pale red dots, and highlights current active page focus sites
    as a bold bright blue dot forced to render last so it always sits on top.
    """
    global_locations = {}

    # 1. Scan directory with robust exception isolation to pull coordinates cleanly
    for json_file in PAGES_DIR.glob("*.json"):
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)

            device_list = []
            if isinstance(data, list):
                device_list = data
            elif isinstance(data, dict):
                if "devices" in data and isinstance(data["devices"], list):
                    device_list = data["devices"]
                else:
                    for val in data.values():
                        if isinstance(val, list) and val and isinstance(val[0], dict):
                            device_list = val
                            break

            for d in device_list:
                try:
                    lat_val = d.get("lat")
                    lon_val = d.get("lon")
                    code = d.get("locationCode", d.get("location_code"))

                    if lat_val is not None and lon_val is not None and code:
                        lat = float(lat_val)
                        lon = float(lon_val)
                        base_code = str(code).split(".")[0].strip().upper()
                        if base_code:
                            global_locations[base_code] = {"lat": lat, "lon": lon}
                except ValueError, TypeError:
                    continue
        except Exception:
            continue

    if not global_locations:
        st.caption("⚠️ *No geographic coordinates available to plot map canvas.*")
        return

    # 2. Extract specific site codes targeted by the current dashboard page
    active_codes = set()
    for d in current_devices:
        for key in ["locationCode", "location_code"]:
            val = d.get(key)
            if val:
                active_codes.add(str(val).split(".")[0].strip().upper())

    # 3. Process into clean presentation blocks (Active Blue vs. Backdrop Pale Red)
    map_data = []
    for code, loc in global_locations.items():
        is_active = code in active_codes

        # Dynamic radius handling based on zoom level
        if zoom is not None and zoom > 8:
            radius = 100 if is_active else 1500
        else:
            radius = 3500 if is_active else 2500

        map_data.append(
            {
                "lat": loc["lat"],
                "lon": loc["lon"],
                # Active site = Sharp Ocean Blue | Background sites = Soft Pale Red (255, 145, 145)
                "color_r": 0 if is_active else 255,
                "color_g": 102 if is_active else 145,
                "color_b": 204 if is_active else 145,
                # Boosted backdrop alpha slightly so the pale red stays cleanly visible against grey landmasses
                "alpha": 255 if is_active else 200,
                "radius": radius,
                "is_active": is_active,  # Maintained for strict rendering z-index sort control
            }
        )

    df = pd.DataFrame(map_data)

    # Sort by is_active ascending (False/0 first, True/1 last)
    # This forces Pydeck to draw the blue dot last, anchoring it cleanly on top!
    if not df.empty:
        df = df.sort_values(by="is_active", ascending=True)

    # 4. Handle auto-centering rules
    current_lats = [
        float(d["lat"]) for d in current_devices if d.get("lat") is not None
    ]
    current_lons = [
        float(d["lon"]) for d in current_devices if d.get("lon") is not None
    ]

    if not center_lat or not center_lon:
        if current_lats and current_lons:
            center_lat = sum(current_lats) / len(current_lats)
            center_lon = sum(current_lons) / len(current_lons)
        else:
            center_lat = df["lat"].mean()
            center_lon = df["lon"].mean()

    if zoom is None:
        if current_lats and current_lons:
            max_span = max(
                max(current_lats) - min(current_lats),
                max(current_lons) - min(current_lons),
            )
            zoom = 12 if max_span < 0.01 else (10 if max_span < 0.1 else 7)
        else:
            zoom = 6

    view_state = pdk.ViewState(
        latitude=center_lat, longitude=center_lon, zoom=zoom, pitch=0, bearing=0
    )

    # 5. Draw the Scatter Layer
    scatterplot_layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position="[lon, lat]",
        get_color="[color_r, color_g, color_b, alpha]",
        get_radius="radius",
        pickable=True,
    )

    st.pydeck_chart(
        pdk.Deck(
            map_style="light", initial_view_state=view_state, layers=[scatterplot_layer]
        )
    )


# ==============================================================================
# --- CONCURRENT PRE-FETCH HELPERS ---
# ==============================================================================
@st.cache_data(ttl=300, show_spinner=False)
def get_onc_annotations(device_ids: tuple) -> dict:
    """Connects to the PostgreSQL DB using secrets.toml credentials

    and fetches collapsed active annotations for all device IDs.
    """
    # 🛑 Exit immediately on Streamlit Cloud (/mount/src exists)
    if os.path.exists("/mount/src"):
        return {}

    if not device_ids:
        return {}

    try:
        conn = st.connection("postgresql", type="sql")
    except Exception as e:
        st.warning(f"Database connection failed: {e}")
        return {}

    id_list = ", ".join(str(int(d)) for d in device_ids)

    query = f"""
        SELECT 
            ah.resourceid,
            ah.startdate,
            STRING_AGG(al.annotation, ' | ' ORDER BY al.annotationlineid DESC) as collapsed_text
        FROM annotation_hdr ah 
        JOIN annotation_line al ON al.annotationhdrid = ah.annotationhdrid 
        WHERE ah.resourceid IN ({id_list})
          AND ah.enddate IS NULL 
        GROUP BY ah.resourceid, ah.annotationhdrid, ah.startdate
        ORDER BY ah.startdate DESC;
    """

    results = {}
    try:
        df = conn.query(query)
        for _, row in df.iterrows():
            dev_id = int(row.iloc[0])
            if dev_id not in results:
                results[dev_id] = []
            results[dev_id].append({"date": row.iloc[1], "text": row.iloc[2]})
    except Exception as e:
        st.warning(f"Failed to query annotations: {e}")

    return results


@st.cache_data(ttl=300, show_spinner=False)
def get_jira_instr_tickets(device_ids: tuple) -> dict:
    """Concurrently fetches open Jira tickets for a list of device IDs.

    Returns a dictionary mapping device_id -> list of ticket dictionaries.
    """
    # 🛑 1. Exit immediately on Streamlit Cloud (/mount/src exists in cloud containers)
    if os.path.exists("/mount/src"):
        return {}

    if not device_ids:
        return {}

    try:
        jira_creds = st.secrets["connections"]["jira"]
        jira = JIRA(
            server=jira_creds["JIRA_SERVER"],
            token_auth=jira_creds["JIRA_PAT"],
            options={"timeout": 3},  # ⏱️ 3-second timeout if local network hangs
            max_retries=0,  # 🚫 No retries
        )
    except Exception as e:
        st.warning(f"Jira Connection failed: {e}")
        return {}

    results = {}

    def fetch_single(dev_id):
        jql = f'project in (Instrumentation, Operations) AND resolution = unresolved AND "Device Id" = {dev_id} ORDER BY createdDate DESC'
        try:
            issues = jira.search_issues(jql, maxResults=10)
            formatted = []
            for i in issues:
                summary = i.fields.summary
                if len(summary) > 100:
                    summary = summary[:97] + "..."

                formatted.append(
                    {
                        "key": i.key,
                        "status": i.fields.status.name,
                        "summary": summary,
                        "link": f"{jira_creds['JIRA_SERVER']}/browse/{i.key}",
                    }
                )
            return dev_id, formatted
        except Exception:
            return dev_id, []

    with ThreadPoolExecutor(max_workers=5) as executor:
        for dev_id, issues in executor.map(fetch_single, device_ids):
            if issues:
                results[dev_id] = issues

    return results


def _fill_gaps_with_nan(df: pd.DataFrame, gap_factor: float = 2.0) -> pd.DataFrame:
    """
    Detects the nominal bin spacing from the median interval.
    Inserts a NaN marker 1 second before the gap ends to cleanly break lines.
    """
    if len(df) < 2:
        return df

    # Detect the nominal bin spacing from the median interval
    intervals = df["datetime"].diff().dt.total_seconds()
    expected_seconds = intervals.median()

    # Create the boolean mask and fill the initial NaN with False
    gap_mask = (intervals > expected_seconds * gap_factor).fillna(False)
    gap_starts = df.loc[gap_mask].index

    nan_rows = []
    for idx in gap_starts:
        # Insert a NaN marker just before the gap-end timestamp
        nan_rows.append(
            {
                "datetime": df.loc[idx, "datetime"] - pd.Timedelta(seconds=1),
                "min": float("nan"),
                "max": float("nan"),
                "avg": float("nan"),
                "qaqcflag": float("nan"),
            }
        )

    if not nan_rows:
        return df

    return (
        pd.concat([df, pd.DataFrame(nan_rows)])
        .sort_values("datetime")
        .reset_index(drop=True)
    )


def _apply_concurrent_scalar_prefetch(
    client: ONCDW, devices_lists: list, date_from: str = "-P7D"
):
    """
    Scans devices for unique sensor IDs, fetches all 7-day scalar data blocks
    concurrently using a ThreadPoolExecutor, and caches them in the ONCDW query layer.
    """
    unique_sensor_ids = set()
    for devices in devices_lists:
        for device in devices:
            for s in device.get("sensors", []):
                if isinstance(s, list):
                    for inner_s in s:
                        if isinstance(inner_s, dict):
                            s_id = inner_s.get("sensorId", inner_s.get("sensor_id"))
                            if s_id:
                                unique_sensor_ids.add(int(s_id))
                elif isinstance(s, dict):
                    s_id = s.get("sensorId", s.get("sensor_id"))
                    if s_id:
                        unique_sensor_ids.add(int(s_id))

    if not unique_sensor_ids:
        return

    d_from, d_to = parse_datetime_parameters(date_from=date_from, date_to=None)

    def pre_fetch_worker(sensor_id):
        try:
            df, ylabel, sensor_type_id = client.widget._query.get_scalar_data(
                source="internal",
                sensor_id=sensor_id,
                date_from=d_from,
                date_to=d_to,
            )
            df = _fill_gaps_with_nan(df)
            return sensor_id, (df, ylabel, sensor_type_id)
        except Exception as e:
            return sensor_id, e

    scalar_data_cache = {}

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(pre_fetch_worker, list(unique_sensor_ids))
        for sensor_id, res in results:
            scalar_data_cache[sensor_id] = res

    orig_get_scalar_data = client.widget._query.get_scalar_data

    # --- NEW: Safe cache for 2W and 1M network queries ---
    @st.cache_data(ttl=300, show_spinner=False)
    def fetch_extended_timeframe(_source, sensor_id, start_date, end_date):
        df, ylabel, sensor_type_id = orig_get_scalar_data(
            source=_source, sensor_id=sensor_id, date_from=start_date, date_to=end_date
        )
        return _fill_gaps_with_nan(df), ylabel, sensor_type_id

    def cached_get_scalar_data(source="internal", **kwargs):
        sensor_id = kwargs.get("sensor_id")
        req_date_from = kwargs.get("date_from")
        req_date_to = kwargs.get("date_to")

        # 1. 7D is returned instantly from memory
        if req_date_from in (d_from, "-P7D") and sensor_id in scalar_data_cache:
            res = scalar_data_cache[sensor_id]
            if isinstance(res, Exception):
                raise res
            df, ylabel, sensor_type_id = res
            return df.copy(), ylabel, sensor_type_id

        # 2. 24H is sliced instantly from 7D cache
        if req_date_from == "-P1D" and sensor_id in scalar_data_cache:
            res = scalar_data_cache[sensor_id]
            if not isinstance(res, Exception):
                df, ylabel, sensor_type_id = res
                if not df.empty:
                    cutoff = df["datetime"].max() - pd.Timedelta(days=1)
                    df_24h = df[df["datetime"] >= cutoff].copy()
                    return df_24h, ylabel, sensor_type_id

        # 3. Safely fallback to cached network request for 2W/1M
        with st.spinner("Fetching extended timeframe..."):
            return fetch_extended_timeframe(
                source, sensor_id, req_date_from, req_date_to
            )

    client.widget._query.get_scalar_data = cached_get_scalar_data
