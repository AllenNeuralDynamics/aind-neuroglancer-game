import streamlit as st
from config import Constants, Pages, UserRoles
from models import User
from utils.dynamodb import initialize_db_managers
from utils.menu import menu

# wide layout
st.set_page_config(layout="wide")

# initialize session state
if "role" not in st.session_state:
    st.session_state.role = None
if "user" not in st.session_state:
    st.session_state.user = None
if "user_manager" or "game_session_manager" not in st.session_state:
    user_manager, game_session_manager = initialize_db_managers()
    st.session_state.user_manager = user_manager
    st.session_state.game_session_manager = game_session_manager

st.title(Constants.APP_NAME.value)

st.header("Log in")

# Role
role = st.selectbox("Select your role", [role.name for role in UserRoles], index=0)

# Username - only required if role is not Guest
username = None
if role != UserRoles.GUEST.name:
    username = st.text_input(
        "Username",
        placeholder="Enter your username",
    )

# Login button with validation
if st.button("Log in", type="primary"):
    if role == UserRoles.GUEST.name:
        st.session_state.role = role
        st.session_state.user = User(
            username=UserRoles.GUEST.value.label,
            email="",
            role=UserRoles.GUEST.value,
        )
        st.switch_page(Pages.HOME.value.link)
    elif username and username.strip():
        st.session_state.role = role
        user = st.session_state.user_manager.get_user(username.strip())
        st.session_state.user = user
        st.switch_page(Pages.HOME.value.link)
    else:
        st.error("Please enter your username")

# Create account button with validation
if role != UserRoles.GUEST.name:
    if st.button("Create account"):
        st.info("User creation is not yet implemented. Please log in as Guest.")


# default menu
menu()
