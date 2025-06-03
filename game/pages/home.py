from pathlib import Path

import streamlit as st
from config import Constants, Pages
from utils.menu import menu_with_redirect, sanity_check_role

# Redirect to login if not logged in, otherwise show the navigation menu
menu_with_redirect()
sanity_check_role(f"pages/{Path(__file__).name}")

st.title(f"Welcome to the {Constants.APP_NAME.value}!")

st.write(
    "This is a game that allows you to explore and annotate brain data using Neuroglancer."
)
st.write("Use the sidebar to navigate to different sections of the app.")

# Single Player and Multiplayer modules
col1, col2 = st.columns(2)

# Single Player
with col1:
    with st.form("single_player_form"):
        st.markdown(
            """
            <div style="padding: 15px; border-radius: 5px;">
                <h3>Single Player</h3>
                <p>Explore a brain and challenge yourself to create annotations on your own.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.form_submit_button("Play Now!"):
            # TODO: Implement single player game
            # Temporarily redirect to demo
            st.switch_page(Pages.DEMO.value.link)
            # st.session_state.page = "Neuroglancer Integration Demo"
            st.rerun()

# Multiplayer
with col2:
    with st.form("multiplayer_form"):
        st.markdown(
            """
          <div style="padding: 15px; border-radius: 5px;">
              <h3>Multiplayer</h3>
              <p>Compete with colleagues in real-time annotation battles.</p>
          </div>
          """,
            unsafe_allow_html=True,
        )
        if st.form_submit_button("Play Now!"):
            # TODO: Implement multiplayer game
            st.write("Multiplayer feature coming soon!")
