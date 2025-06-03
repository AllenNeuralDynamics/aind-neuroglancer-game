import streamlit as st
from config import Constants, Pages, UserRoles
from utils.menu import menu

# wide layout
st.set_page_config(layout="wide")

# initialize session state
if "role" not in st.session_state:
    st.session_state.role = None

st.title(Constants.APP_NAME.value)

# Log in
st.header("Log in")
role = st.selectbox("Select your role", [role.name for role in UserRoles], index=0)
if st.button("Log in"):
    st.session_state.role = role
    st.switch_page(Pages.HOME.value.link)

# default menu
menu()
