import streamlit as st
from utils.menu import menu_with_redirect

# Redirect to login if not logged in, otherwise show the navigation menu
menu_with_redirect()

st.title("Leaderboard")

st.write("This page will display the leaderboard for the Neuroglancer Game.")
st.write("Feature coming soon!")
