from pathlib import Path

import streamlit as st
from models import User
from utils.menu import menu_with_redirect, sanity_check_role

# Redirect to login if not logged in, otherwise show the navigation menu
menu_with_redirect()
sanity_check_role(f"pages/{Path(__file__).name}")

st.title("My Account")

user: User | None = st.session_state.get("user")

if not user:
    st.error("User not found in session state. Please log in again.")
else:
    st.subheader(f"Welcome, {user.username}!")

    # show user info from session state - username, email
    st.text_input("Username", value=user.username, disabled=True)
    st.text_input("Email", value=user.email, disabled=True)
    st.text_input("Role", value=user.role.label, disabled=True)

