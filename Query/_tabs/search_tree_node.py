import json
from pathlib import Path

import streamlit as st
from _service import get_search_tree_node_code_id_dict_from_database

from _tabs._json_update_helpers import build_json_diff, read_json_file

SEARCH_TREE_NODE_JSON_PATH = Path("./Query/search_tree_node.json")
SEARCH_TREE_NODE_PENDING_KEY = "pending_search_tree_node_update"
SEARCH_TREE_NODE_DIFF_KEY = "pending_search_tree_node_diff"


@st.dialog("Update searchTreeNode")
def update_search_tree_node_dialog():
    st.text("This will query the PROD database to update the searchTreeNode json file.")
    st.markdown(
        "Make sure you are on the dev server in the local internet or connected to the VPN, not on the :red[**Streamlit Community Cloud**]."
    )
    st.text(
        "You need to restart the app to apply changes. Also you probably want to push the changes to GitHub after updating."
    )
    st.text("Click the x icon to cancel.")

    if st.button("Proceed?", type="primary", key="search_tree_node_proceed"):
        try:
            updated_search_tree_node = get_search_tree_node_code_id_dict_from_database()
            st.success("Retrieved searchTreeNode from database successfully.")

            current_search_tree_node = read_json_file(SEARCH_TREE_NODE_JSON_PATH)
            diff_text = build_json_diff(
                current_search_tree_node,
                updated_search_tree_node,
                file_name="search_tree_node.json",
            )

            if not diff_text:
                st.info("No changes detected. search_tree_node.json was not modified.")
                st.session_state.pop(SEARCH_TREE_NODE_PENDING_KEY, None)
                st.session_state.pop(SEARCH_TREE_NODE_DIFF_KEY, None)
            else:
                st.session_state[SEARCH_TREE_NODE_PENDING_KEY] = updated_search_tree_node
                st.session_state[SEARCH_TREE_NODE_DIFF_KEY] = diff_text
                st.warning("Differences found. Review and accept to apply changes.")
        except Exception as e:
            st.error(f"Error retrieving searchTreeNode dictionary: {e}")

    pending_update = st.session_state.get(SEARCH_TREE_NODE_PENDING_KEY)
    diff_text = st.session_state.get(SEARCH_TREE_NODE_DIFF_KEY)
    if pending_update and diff_text:
        st.markdown("### Proposed changes")
        st.code(diff_text, language="diff")
        accept_col, reject_col = st.columns(2)

        with accept_col:
            if st.button("Accept changes", type="primary", key="search_tree_node_accept"):
                with SEARCH_TREE_NODE_JSON_PATH.open("w") as f:
                    json.dump(pending_update, f, indent=4)
                st.success("Updated search_tree_node.json successfully.")
                st.session_state.pop(SEARCH_TREE_NODE_PENDING_KEY, None)
                st.session_state.pop(SEARCH_TREE_NODE_DIFF_KEY, None)

        with reject_col:
            if st.button("Reject changes", key="search_tree_node_reject"):
                st.session_state.pop(SEARCH_TREE_NODE_PENDING_KEY, None)
                st.session_state.pop(SEARCH_TREE_NODE_DIFF_KEY, None)
                st.info("Changes discarded.")


def search_tree_node_tab():
    if st.button("Update searchTreeNode dictionary", type="primary"):
        update_search_tree_node_dialog()

    location_code = st.text_input("Query searchTreeNodeId by location code:")

    if st.button("Get searchTreeNodeId"):
        if location_code:
            search_tree_node_id = st.session_state["search_tree_node"].get(
                location_code
            )
            if search_tree_node_id:
                st.success(
                    f"searchTreeNodeId for location code '{location_code}': {search_tree_node_id}"
                )
            else:
                st.error(
                    f"Location code '{location_code}' not found in the dictionary."
                )
        else:
            st.warning("Please enter a location code.")
