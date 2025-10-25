"""Utility functions for managing game state in session_state.

Prior to starting the game, game_options should be set in session_state

During the game, we will set in session_state:
- current_round: int, the current round number
- seconds_left: int, seconds left in the current round
- round_started: bool, whether the round is currently active
- viewer: neuroglancer.Viewer, the neuroglancer viewer instance
- viewer_url: str, the URL of the neuroglancer viewer
- game_summary: dict, summary of the game so far

These should be cleared at the end of the game or when the user exits the game
"""

import streamlit as st
from config import Constants
from utils.neuroglancer import get_annotations_from_state
from models import GameSession

######### Get game state from session_state #########


def get_game_options_from_session_state() -> dict:
    """Retrieve game options from session_state. If not found, stop execution."""
    game_options = dict()
    if "game_options" in st.session_state:
        game_options = st.session_state.game_options
    else:
        st.error("No game options selected. Please select a game in the Home page.")
        st.stop()
    return game_options


######### Update game state in session_state #########


def start_round(round_number: int, mins_per_round: int) -> None:
    """Initialize the game state for a new round."""
    st.session_state.current_round = round_number
    st.session_state.seconds_left = mins_per_round * 60
    st.session_state.round_started = True
    # Full rerun to update the page
    st.rerun()


def process_round_timer() -> None:
    """Decrement the countdown timer for the current round.
    If the timer reaches zero, stop the round and save the annotations.
    """
    if st.session_state.round_started:
        st.session_state.seconds_left -= Constants.GAME_STATUS_REFRESH_EVERY.value

    # If time is up, stop the round and save the annotations from this round
    if st.session_state.round_started and st.session_state.seconds_left <= 0:
        st.session_state.round_started = False
        # TODO: get annotations from current round rather than total
        annotations = (
            get_annotations_from_state(st.session_state.viewer.state)
            if "viewer" in st.session_state
            else []
        )
        if "game_summary" not in st.session_state:
            st.session_state.game_summary = dict()
        st.session_state.game_summary[st.session_state.current_round] = {
            "num_annotations": len(annotations),
            "annotations": annotations,
        }
        # Full rerun to update the page
        st.rerun()


def start_game():
    """Initalize and start the first round of the game if not already started."""
    if "round_started" not in st.session_state:
        game_options = get_game_options_from_session_state()
        # Create GameSession object
        game_session = GameSession(
            username=st.session_state.user.username,
            game_mode=game_options.get("game_mode", ""),
            num_rounds=game_options.get("num_rounds", 0),
            time_per_round=game_options.get("time_per_round", 0),
        )
        st.session_state.game_session = game_session
        # Start the game with first round
        game_session.start_game()
        # Save the active game session to db
        st.session_state.game_session_manager.create_session(game_session)
        start_round(1, game_options.get("time_per_round"))


def end_game():
    """Clear game state from session_state."""
    # Mark the game session as ended
    if "game_session" in st.session_state:
        # NOTE: summary is only calculated at end of each round
        total_annotations = sum(
            summary["num_annotations"]
            for summary in st.session_state.get("game_summary", {}).values()
        )
        st.session_state.game_session.end_game(total_annotations)
        # Save the completed game session to db
        st.session_state.game_session_manager.create_session(st.session_state.game_session)
    # TODO: delete the viewer instance if needed
    keys_to_clear = [
        "current_round",
        "seconds_left",
        "round_started",
        "viewer",
        "viewer_url",
        "game_summary",
        "game_options",
        "game_session",
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
