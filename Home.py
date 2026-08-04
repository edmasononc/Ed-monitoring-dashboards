import streamlit as st

st.set_page_config(page_title="DAQ Dashboard")
st.title("Welcome to Ed's monitoring dashboard!")
st.write(
    "For individual instrument dashboards - Please select a dashboard from the sidebar. Click There 👈"
)

#st.write("----")

#st.write("Below are some **_links_** to public ONC dashboards")

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

# --- Your actual Streamlit link button ---
#st.link_button(
   #"ONCs General Earthquake Dashboard",
    #"https://www.oceannetworks.ca/data/data-dashboards/earthquake-data-dashboard/",
#)

#st.link_button(
   # "ONCs Endeavour Earthquake Catalog",
   # "https://data.oceannetworks.ca/EndeavourEarthquakeCatalog",
#)

#st.image("https://cdn.pixabay.com/photo/2011/12/13/14/28/earth-11009_1280.jpg")
