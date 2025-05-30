import streamlit as st
from utils.menu import menu_with_redirect

# Redirect to login if not logged in, otherwise show the navigation menu
menu_with_redirect()

st.title("Account")

st.write("This page will allow users to manage their account settings.")
st.write("Feature coming soon!")
