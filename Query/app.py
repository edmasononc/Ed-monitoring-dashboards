import json

import streamlit as st
from _tabs import (
    device_id_tab,
    location_children_tab,
    search_tree_node_tab,
    sensor_code_tab,
)

if "search_tree_node" not in st.session_state:
    with open("./Query/search_tree_node.json") as f:
        st.session_state["search_tree_node"] = json.load(f)

if "sensor_code" not in st.session_state:
    with open("./Query/sensor_code.json") as f:
        st.session_state["sensor_code"] = json.load(f)


tab1, tab2, tab3, tab4 = st.tabs(
    ["Device Info", "Loc Children", "Search Tree Node", "Sensor Code"]
)

with tab1:
    device_id_tab()

with tab2:
    location_children_tab()

with tab3:
    search_tree_node_tab()

with tab4:
    sensor_code_tab()
