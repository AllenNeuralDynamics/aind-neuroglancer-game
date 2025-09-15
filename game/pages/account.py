from pathlib import Path

import streamlit as st
from utils.menu import menu_with_redirect, sanity_check_role

# Redirect to login if not logged in, otherwise show the navigation menu
menu_with_redirect()
sanity_check_role(f"pages/{Path(__file__).name}")

st.title("My Account")

st.subheader(f"Welcome, {st.session_state.get('username', 'unknown user')}!")

st.write("This page will allow users to manage their account settings.")
st.write("Feature coming soon!")
