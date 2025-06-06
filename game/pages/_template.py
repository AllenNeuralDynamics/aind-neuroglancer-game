"""Template for a Streamlit page with a navigation menu and role check."""
from pathlib import Path

import streamlit as st
from utils.menu import menu_with_redirect, sanity_check_role

# Redirect to login if not logged in, otherwise show the navigation menu
menu_with_redirect()
sanity_check_role(f"pages/{Path(__file__).name}")

st.title("Page Title")
st.markdown(f"You are currently logged with the role of {st.session_state.role}.")
