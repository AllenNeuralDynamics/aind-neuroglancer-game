"""Single Player Game Page"""
from pathlib import Path

import streamlit as st
from utils.menu import menu_with_redirect, sanity_check_role

# Redirect to login if not logged in, otherwise show the navigation menu
menu_with_redirect()
sanity_check_role(f"pages/{Path(__file__).name}")

st.title("Single Player Game")

st.write("This page will allow users to play in single-player mode.")
st.write("Feature coming soon!")

# Selected game options
if "game_options" in st.session_state:
    game_options = st.session_state.game_options
    # TESTING: display entire game_options dictionary
    st.write("**Selected Game Options:**", game_options)
else:
    st.error("No game options selected. Please select a game in the Home page.")

