import streamlit as st
from config import Pages, UserRoles


def menu_with_redirect():
    """Redirect to main page if not logged in, otherwise render nav menu"""
    if "role" not in st.session_state or st.session_state.role is None:
        st.switch_page(Pages.LOGIN.value.link)
    menu()


def menu():
    """Redirect to correct menu based on session state"""
    if "role" not in st.session_state or st.session_state.role is None:
        login_menu()
        return
    authenticated_menu()


def authenticated_menu():
    """Display navigation menu for authenticated users"""
    role = st.session_state.role
    if role not in UserRoles.__members__:
        st.error(f"Unknown role: {role}")
        return
    user_role = UserRoles[role]
    for page in user_role.value.allowed_pages:
        st.sidebar.page_link(page=page.link, label=page.label, icon=page.icon)


def login_menu():
    """Display navigation menu for unauthenticated users"""
    page = Pages.LOGIN.value
    st.sidebar.page_link(page=page.link, label=page.label, icon=page.icon)