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


@st.dialog("Game Options")
def create_user(role: str):
    """Dialog for new user account"""
    st.header(f"Create {role} account", divider="rainbow")
    # TODO: remove warning once auth is implemented
    st.warning(
        "Please DO NOT provide any sensitive info! Authentication is not implemented yet!"
    )

    # Inputs - Role, username, email
    st.text_input("Role", value=role, disabled=True)
    username = st.text_input(
        "Username",
        placeholder="Enter your desired username",
    )
    email = st.text_input(
        "Email",
        placeholder="Enter your email address",
    )

    if st.button("Create & Log in", type="primary", use_container_width=True):
        if username and username.strip() and email and email.strip():
            st.session_state.role = role
            user = User(
                username=username.strip(),
                email=email.strip(),
                role=UserRoles[role].value,
            )
            created_user = st.session_state.user_manager.create_user(user)
            st.session_state.user = created_user
            st.switch_page(Pages.HOME.value.link)
        else:
            st.error("Please enter a valid username and email")


if role != UserRoles.GUEST.name:
    if st.button("Create account"):
        create_user(role)


# default menu
menu()
