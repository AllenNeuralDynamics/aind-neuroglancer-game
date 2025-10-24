from pathlib import Path

import streamlit as st
from config import Constants, GameModes
from models import GameMode
from utils.menu import menu_with_redirect, sanity_check_role

# Redirect to login if not logged in, otherwise show the navigation menu
menu_with_redirect()
sanity_check_role(f"pages/{Path(__file__).name}")

st.title(f"Welcome to the {Constants.APP_NAME.value}!")
st.write("Choose your game mode to start exploring.")


@st.dialog("Game Options")
def show_game_options(game_mode: GameMode):
    """Dialog for single player game options."""
    st.header(game_mode.label, divider="rainbow")
    st.caption(game_mode.description)
    # inputs for game options
    num_rounds = st.number_input(
        "Number of rounds",
        min_value=1,
        max_value=5,
        value=3,
        step=1,
        help="How many rounds you want to play",
    )
    time_per_round = st.number_input(
        "Time per round (minutes)",
        min_value=1,
        max_value=10,
        value=3,
        step=1,
        help="How long each round will last",
    )
    # Example additional options
    # allow_movement = st.radio(
    #     "Allow move",
    #     options=[True, False],
    #     format_func=lambda x: "Yes" if x else "No",
    #     index=0,
    #     help="Whether you can move around the brain during the game.",
    # )
    # allow_zoom = st.radio(
    #     "Allow zoom",
    #     options=[True, False],
    #     format_func=lambda x: "Yes" if x else "No",
    #     index=0,
    #     help="Whether you can zoom in/out of the brain during the game.",
    # )
    # start game button
    if st.button("Start game", use_container_width=True):
        # save game options to session state
        st.session_state.game_options = {
            "game_mode": game_mode.label,
            "num_rounds": num_rounds,
            "time_per_round": time_per_round,
            # "allow_movement": allow_movement,
            # "allow_zoom": allow_zoom,
        }
        # redirect to the game page
        if game_mode.link is None:
            st.error("This game mode is not implemented yet.")
        else:
            st.switch_page(game_mode.link)


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
                container.button(
                    label="Coming soon",
                    key=f"play_{modes[idx].name}",
                    disabled=True,
                    icon=":material/schedule:",
                    use_container_width=True,
                )
            else:
                if container.button(
                    label="Play now",
                    key=f"play_{modes[idx].name}",
                    icon=":material/sports_esports:",
                    use_container_width=True,
                ):
                    # TODO: consider https://docs.streamlit.io/develop/api-reference/execution-flow/st.dialog
                    if game_mode.link is None:
                        st.error("This game mode is not implemented yet.")
                    else:
                        show_game_options(game_mode)
