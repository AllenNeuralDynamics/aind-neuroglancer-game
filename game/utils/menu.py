"""Utility functions for rendering navigation and game menus."""

import streamlit as st
from config import Constants, Pages, UserRoles
from models import User
from utils.game import end_game


def menu_with_redirect(show_game_menu: bool = False):
    """Redirect to main page if not logged in, otherwise render nav menu"""
    if "role" not in st.session_state or st.session_state.role is None:
        st.switch_page(Pages.LOGIN.value.link)
    menu(show_game_menu)


def menu(show_game_menu: bool = False):
    """Redirect to correct menu based on session state"""
    if "role" not in st.session_state or st.session_state.role is None:
        _login_menu()
        return
    _authenticated_menu(show_game_menu)


def _authenticated_menu(show_game_menu):
    """Display navigation or game menu for authenticated users"""
    role = st.session_state.role
    if role not in UserRoles.__members__:
        st.error(f"Unknown role: {role}")
        return
    if show_game_menu:
        # Game menu: game options, exit
        if "game_options" in st.session_state:
            game_options = st.session_state.game_options
            st.sidebar.header(game_options["game_mode"], divider="rainbow")
            for k, v in game_options.items():
                if k != "game_mode":
                    st.sidebar.caption(f"**{k.replace('_', ' ').title()}**: {v}")
            st.sidebar.divider()
        if st.sidebar.button(
            "Exit Game", icon=":material/exit_to_app:", use_container_width=True
        ):
            end_game()
            st.switch_page(Pages.HOME.value.link)
    else:
        # Nav menu: page links, logout
        user_role = UserRoles[role]
        st.sidebar.header(Constants.APP_NAME.value, divider="rainbow")
        for page in user_role.value.allowed_pages:
            st.sidebar.page_link(page=page.link, label=page.label, icon=page.icon)
        st.sidebar.divider()
        user: User | None = st.session_state.get("user")
        st.sidebar.write(f"Logged in as **{user.username if user else role}**")
        if st.sidebar.button("Log out", icon=":material/login:"):
            st.session_state.role = None
            st.session_state.user = None
            st.switch_page(Pages.LOGIN.value.link)


def _login_menu():
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
    if link not in user_role.value.allowed_links:
        st.error("You do not have permission to view this page.")
        st.stop()
        return
