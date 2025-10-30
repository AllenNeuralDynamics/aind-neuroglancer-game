"""Single Player Game Page"""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from config import Constants, Pages
from utils.game import (
    save_game,
    clear_game,
    get_game_options_from_session_state,
    process_round_timer,
    start_game,
    start_round,
)
from utils.menu import menu_with_redirect, sanity_check_role
from utils.neuroglancer import (
    create_default_viewer,
    get_annotations_from_state,
    get_viewer_url,
)

# Redirect to login if not logged in, otherwise show the navigation menu
menu_with_redirect(show_game_menu=True)
sanity_check_role(f"pages/{Path(__file__).name}")

GAME_OPTIONS = get_game_options_from_session_state()


# Initialize and start the first round
start_game()

# Set the timer fragment to run every second if the round is started
if st.session_state.round_started:
    run_every = Constants.GAME_STATUS_REFRESH_EVERY.value
else:
    run_every = None


@st.fragment(run_every=run_every)
def update_game_status():
    """Fragment to update countdown timer and display game status"""
    process_round_timer()
    if st.session_state.round_started:
        annotations = (
            get_annotations_from_state(st.session_state.viewer.state)
            if "viewer" in st.session_state
            else []
        )
        num_annotations = len(annotations)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.caption("⏳ Time Left")
            st.write(
                f"{st.session_state.seconds_left // 60:02}:{st.session_state.seconds_left % 60:02}"
            )
        with col2:
            st.caption("Round")
            st.write(
                f"{st.session_state.current_round}/{GAME_OPTIONS.get('num_rounds')}"
            )
        with col3:
            st.caption("Annotations")
            st.write(num_annotations)


# Display the game status and timer
update_game_status()

# Display the neuroglancer viewer or game summary
if st.session_state.round_started:
    # Create the initial neuroglancer viewer if needed
    if "viewer_url" not in st.session_state:
        viewer = create_default_viewer()
        viewer_url = get_viewer_url(viewer)
        st.session_state.viewer = viewer
        st.session_state.viewer_url = viewer_url
    # Display the neuroglancer viewer iframe
    components.iframe(
        src=st.session_state.viewer_url,
        width=1000,
        height=1000,
    )
else:
    # Display the game summary and next buttons
    current_round = st.session_state.current_round
    current_num_annotations = st.session_state.game_summary[current_round][
        "num_annotations"
    ]
    num_rounds = GAME_OPTIONS.get("num_rounds")
    total_num_annotations = sum(
        summary["num_annotations"]
        for summary in st.session_state.get("game_summary", {}).values()
    )
    st.subheader(f"Time's up for Round {current_round}/{num_rounds}!")
    if current_round < num_rounds:
        # User has more rounds to play but still save current progress to db
        save_game(
            total_annotations=total_num_annotations,
            end_game=False,
            is_abandoned=False
        )
        # Display round summary and next round button
        st.info(f"You made {current_num_annotations} annotations this round.")
        with st.expander("Show current summary"):
            st.json(st.session_state.game_summary)
        if st.button("Start Next Round", type="primary"):
            start_round(
                st.session_state.current_round + 1, GAME_OPTIONS.get("time_per_round")
            )
    else:
        # User has completed all rounds. Save the game to Db
        save_game(
            total_annotations=total_num_annotations,
            end_game=True,
            is_abandoned=False
        )
        # Display final summary and options
        st.balloons()
        st.success(
            f"Thank you for playing! You made a total of {total_num_annotations} annotations."
        )
        with st.expander("Show game summary"):
            st.json(st.session_state.game_summary)
        # TODO: Save results to S3 and leaderboard
        if st.button("Submit Results", type="primary"):
            st.info("Feature coming soon!")
        # TODO: Allow users to download their results
        if st.button("Download Results"):
            st.info("Feature coming soon!")
        if st.button("Exit Game"):
            clear_game()
            st.switch_page(Pages.HOME.value.link)
