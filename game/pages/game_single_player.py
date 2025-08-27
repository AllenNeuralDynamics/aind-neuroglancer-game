"""Single Player Game Page"""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from config import Constants
from utils.menu import menu_with_redirect, sanity_check_role
from utils.neuroglancer import (
    create_default_viewer,
    get_annotations_from_state,
    get_viewer_url,
)

# Redirect to login if not logged in, otherwise show the navigation menu
menu_with_redirect(show_game_menu=True)
sanity_check_role(f"pages/{Path(__file__).name}")

# Selected game options
if "game_options" in st.session_state:
    game_options = st.session_state.game_options
else:
    st.error("No game options selected. Please select a game in the Home page.")
    st.stop()

def start_round(round_number: int):
    """Initialize the game state for a new round."""
    st.session_state.current_round = round_number
    st.session_state.seconds_left = game_options.get("time_per_round") * 60
    st.session_state.round_started = True


# Initialize and start the first round
if "round_started" not in st.session_state:
    start_round(1)

# Set the timer fragment to run every second if the round is started
if st.session_state.round_started:
    run_every = Constants.GAME_STATUS_REFRESH_EVERY.value
else:
    run_every = None

@st.fragment(run_every=run_every)
def update_game_status():
    # Update countdown timer and display game status
    if st.session_state.round_started:
        st.session_state.seconds_left -= Constants.GAME_STATUS_REFRESH_EVERY.value
        annotations = get_annotations_from_state(st.session_state.viewer.state) if "viewer" in st.session_state else []
        st.table(
            {
                "Round": [
                    f"{st.session_state.current_round}/{game_options.get('num_rounds')}"
                ],
                "Time Left": [
                    f"{st.session_state.seconds_left // 60:02}:{st.session_state.seconds_left % 60:02}"
                ],
                "Annotations": [len(annotations)],
            }
        )
    # If time is up, stop the round and save the annotations from this round
    if st.session_state.seconds_left <= 0 and st.session_state.round_started:
        st.session_state.round_started = False
        if "game_summary" not in st.session_state:
            st.session_state.game_summary = dict()
        st.session_state.game_summary[st.session_state.current_round] = {
            "num_annotations": len(annotations),
            "annotations": annotations,
        }
        # Full rerun to update the page
        st.rerun()


# Display the game status and timer
update_game_status()

# Display the neuroglancer viewer or game summary
if st.session_state.round_started:
    # Create the initial neuroglancer viewer if needed
    if "viewer_url" not in st.session_state:
        viewer = create_default_viewer()
        viewer_url = get_viewer_url(viewer)
        st.session_state.viewer = viewer
        st.session_state.viewer_url = viewer_url
    # Display the neuroglancer viewer iframe
    components.iframe(
        src=st.session_state.viewer_url,
        width=1000,
        height=1000,
    )
else:
    # Display the summary of the current round
    st.write("Time is up for the current round!")
    st.write("Game Summary so far:")
    st.json(st.session_state.game_summary)