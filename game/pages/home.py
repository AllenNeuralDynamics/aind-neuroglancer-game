import streamlit as st
from utils.menu import menu_with_redirect

# Redirect to login if not logged in, otherwise show the navigation menu
menu_with_redirect()

st.title("Home")

st.write("This page will be the home page to start games.")
st.write("Feature coming soon!")
