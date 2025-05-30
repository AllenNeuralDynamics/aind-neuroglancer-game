import streamlit as st
from utils.menu import menu_with_redirect

# Redirect to login if not logged in, otherwise show the navigation menu
menu_with_redirect()

st.title("Demo")

st.write("This page will demo the neuroglancer python integration.")
st.write("Feature coming soon!")
