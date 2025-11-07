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
    st.text_input("Role", value=user.role, disabled=True)
    if user.join_date:
        st.text_input("Member since", value=user.join_date.isoformat(), disabled=True)
    else:
        st.text_input("Member since", value="N/A", disabled=True)

    # Basic metrics
    total_games = st.session_state.game_session_manager.count_sessions_for_user(
        user.username
    )
    total_annotations = (
        st.session_state.game_session_manager.get_total_annotations_for_user(
            user.username
        )
    )
    col1, col2, col3 = st.columns(3)
    col1.metric("Total games played", total_games)
    col2.metric("Total annotations made", total_annotations)
    # TODO: other metrics
    col3.metric("Average accuracy", "0%")
