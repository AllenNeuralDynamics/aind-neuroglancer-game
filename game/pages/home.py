from pathlib import Path

import streamlit as st
from config import Constants, GameModes
from utils.menu import menu_with_redirect, sanity_check_role

# Redirect to login if not logged in, otherwise show the navigation menu
menu_with_redirect()
sanity_check_role(f"pages/{Path(__file__).name}")

st.title(f"Welcome to the {Constants.APP_NAME.value}!")
st.write("Choose your game mode to start exploring.")

# Grid layout for game modes
modes = list(GameModes)
num_cols = 3
rows = (len(modes) + num_cols - 1) // num_cols

for row in range(rows):
    cols = st.columns(num_cols)
    for col in range(num_cols):
        idx = row * num_cols + col
        if idx >= len(modes):
            break
        game_mode = modes[idx].value
        with cols[col]:
            container = st.container(height=250)
            # label and description
            container.subheader(game_mode.label, divider="rainbow")
            if game_mode.is_learning_mode:
                container.badge("Learning mode", icon=":material/school:")
            container.caption(game_mode.description)
            # play or coming soon button
            if game_mode.disabled:
                container.button(label="Coming soon", key=f"play_{modes[idx].name}", disabled=True, icon=":material/schedule:",use_container_width=True)
            else:
                if container.button(
                    label="Play now", key=f"play_{modes[idx].name}", icon=":material/sports_esports:",use_container_width=True
                ):
                    # TODO: consider https://docs.streamlit.io/develop/api-reference/execution-flow/st.dialog
                    if game_mode.link is None:
                        st.error("This game mode is not implemented yet.")
                    else:
                        st.switch_page(game_mode.link)
