"""Single Player Game Page"""
from pathlib import Path

import streamlit as st
from config import Constants
from utils.menu import menu_with_redirect, sanity_check_role

# Redirect to login if not logged in, otherwise show the navigation menu
menu_with_redirect(show_game_menu=True)
sanity_check_role(f"pages/{Path(__file__).name}")

# Selected game options
if "game_options" in st.session_state:
    game_options = st.session_state.game_options
else:
    st.error("No game options selected. Please select a game in the Home page.")
    st.stop()

# Start the current round and set remaining time
if "round_started" not in st.session_state:
    st.session_state.current_round = 1
    st.session_state.seconds_left = game_options.get("time_per_round") * 60
    st.session_state.round_started = True


@st.fragment(run_every=Constants.GAME_STATUS_REFRESH_EVERY.value)
def update_game_status():
    # Update countdown timer
    if st.session_state.round_started:
        st.session_state.seconds_left -= Constants.GAME_STATUS_REFRESH_EVERY.value
    # display game status: Round, Time Left, Annotations
    st.table(
        {
            "Round": [
                f"{st.session_state.current_round}/{game_options.get('num_rounds')}"
            ],
            "Time Left": [
                f"{st.session_state.seconds_left // 60:02}:{st.session_state.seconds_left % 60:02}"
            ],
            "Annotations": [0],  # TODO: pull from viewer state!
        }
    )
    # If time is up, stop the round
    if st.session_state.seconds_left <= 0:
        st.write("Time is up for the current round!")
        st.session_state.round_started = False
        st.stop()


update_game_status()