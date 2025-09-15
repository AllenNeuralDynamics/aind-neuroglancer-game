import streamlit as st
from config import Constants, Pages, UserRoles
from utils.menu import menu

# wide layout
st.set_page_config(layout="wide")

# initialize session state
if "role" not in st.session_state:
    st.session_state.role = None
if "username" not in st.session_state:
    st.session_state.username = None

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
        st.session_state.username = UserRoles.GUEST.value.label
        st.switch_page(Pages.HOME.value.link)
    elif username and username.strip():
        st.session_state.role = role
        st.session_state.username = username.strip()
        st.switch_page(Pages.HOME.value.link)
    else:
        st.error("Please enter your username")

# Create account button with validation
if role != UserRoles.GUEST.name:
    if st.button("Create account"):
        st.info("User creation is not yet implemented. Please log in as Guest.")


# default menu
menu()
