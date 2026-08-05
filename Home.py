import os

# 🛑 ULTIMATE GUARD: Instantly intercept and fail any hidden Jira requests on Streamlit Cloud
if os.path.exists("/mount/src"):
    import requests

    _original_request = requests.Session.request

    def _fast_fail_jira(self, method, url, *args, **kwargs):
        if url and "jira.oceannetworks.ca" in str(url):
            raise requests.exceptions.ConnectionError(
                "Jira is blocked on Streamlit Cloud"
            )
        return _original_request(self, method, url, *args, **kwargs)

    requests.Session.request = _fast_fail_jira

import streamlit as st

st.set_page_config(page_title="DAQ Dashboard")
st.title("Welcome to Ed's monitoring dashboard!")
st.write(
    "For individual instrument dashboards - Please select a dashboard from the sidebar. Click There 👈"
)
st.write("Current Working Directory:", os.getcwd())
st.write("Does /mount/src exist?", os.path.exists("/mount/src"))
# --- Custom CSS for st.link_button ---
st.markdown(
    """
    <style>
    /* Select the link button by its data-testid */
    div[data-testid="stLinkButton"] > a {
        background-color: #0072ff !important;  /* Button color */
        color: white !important;               /* Text color */
        padding: 0.6em 1.2em;
        border-radius: 6px;
        text-decoration: none;
        font-size: 16px;
    }

    div[data-testid="stLinkButton"] > a:hover {
        background-color: #0058c7 !important;  /* Hover color */
        color: white !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)