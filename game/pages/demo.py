import json
import os
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from utils.menu import menu_with_redirect, sanity_check_role
from utils.neuroglancer import (
    create_default_viewer,
    download_s3_state_config,
    json_dump_to_viewer_state,
    url_to_viewer_state,
    viewer_state_to_json_dump,
)

CURR_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

# External neuroglancer URLs
EXTERNAL_DOMAIN = "http://52.43.100.13:8080"  # alternatively use "https://neuroglancer-demo.appspot.com" or current gcloud deployment
TEST_DATASET_CONFIG = "s3://aind-open-data-dev-u5u0i5/SmartSPIM_660851_2023-04-03_16-25-48_stitched_2025-01-17_00-58-31/neuroglancer_config.json"
EXTERNAL_TEST_DATASET_URL = f"{EXTERNAL_DOMAIN}/#!{TEST_DATASET_CONFIG}?"


# Redirect to login if not logged in, otherwise show the navigation menu
menu_with_redirect()
sanity_check_role(f"pages/{Path(__file__).name}")

st.title("Neuroglancer Integration Demo")


# create default neuroglancer
def create_initial_viewer():
    viewer = create_default_viewer()
    viewer_url = viewer.get_viewer_url()
    # store viewer in session state
    if "viewer" not in st.session_state or st.session_state.viewer is None:
        st.session_state.viewer = viewer
        st.session_state.viewer_url = viewer_url


# input box for an external neuroglancer URL
st.write("Enter an External Neuroglancer URL:")
external_url = st.text_input("External Neuroglancer URL")

# if the user enters a URL, parse the state and statejson from url
if external_url:
    viewer_state = url_to_viewer_state(external_url)
    json_dump = viewer_state_to_json_dump(viewer_state)
    st.json(json_dump)
    if "viewer" not in st.session_state:
        viewer = create_default_viewer()
    viewer = st.session_state.viewer
    viewer.set_state(viewer_state)

# input box for s3 location
s3_location = st.text_input("S3 Location", placeholder=TEST_DATASET_CONFIG)
if s3_location:
    contents = download_s3_state_config(s3_location)
    st.json(contents)
    viewer_state = json_dump_to_viewer_state(json_dump=contents)
    viewer = st.session_state.viewer
    viewer.set_state(viewer_state)

# button to load state from initial_state.json
if st.button("Load initial state from initial_state.json (Hackathon example)"):
    dir = CURR_DIR.parent / "initial_state.json"
    with open(dir, "r") as f:
        initial_state = json.load(f)
    viewer = st.session_state.viewer
    viewer.set_state(initial_state)

# display viewer_url
st.write(f"Viewer URL: {st.session_state.get('viewer_url', None)}")

# display viewer in iframe
if "viewer_url" in st.session_state:
    components.iframe(
        src=st.session_state.viewer_url,
        width=1000,
        height=1000,
    )
else:
    create_initial_viewer()
    components.iframe(
        src=st.session_state.viewer_url,
        width=1000,
        height=1000,
    )

# Button to get most recent iframe URL
if st.button("Show current URL"):
    if "viewer_url" in st.session_state:
        viewer_url = st.session_state.viewer_url
        st.write(viewer_url)
    else:
        st.write("No viewer found in session state.")

if st.button("Show current state"):
    if "viewer" in st.session_state:
        viewer = st.session_state.viewer
        json_dump = viewer_state_to_json_dump(viewer.state)
        st.json(json_dump)
    else:
        st.write("No viewer found in session state.")
