import streamlit as st
from config import Constants, Pages, UserRoles


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
    st.sidebar.header(Constants.APP_NAME.value, divider="rainbow")
    for page in user_role.value.allowed_pages:
        st.sidebar.page_link(page=page.link, label=page.label, icon=page.icon)

    # Logout button at bottom of sidebar
    st.sidebar.divider()
    st.sidebar.write(f"Logged in as **{role}**")
    if st.sidebar.button("Log out", icon=":material/login:"):
        st.session_state.role = None
        st.switch_page(Pages.LOGIN.value.link)


def login_menu():
    """Display navigation menu for unauthenticated users"""
    page = Pages.LOGIN.value
    st.sidebar.header(Constants.APP_NAME.value, divider="rainbow")
    st.sidebar.page_link(page=page.link, label=page.label, icon=page.icon)


def sanity_check_role(link: str):
    """Sanity check to verify current user role is allowed to access a given page"""
    role = st.session_state.get("role", "Unknown")
    if role not in UserRoles.__members__:
        st.error(f"Unknown role: {role}")
        st.stop()
        return
    user_role = UserRoles[role]
    allowed_pages = user_role.value.allowed_pages
    if link not in [page.link for page in allowed_pages]:
        st.error(f"You do not have permission to view this page.")
        st.stop()
        return
