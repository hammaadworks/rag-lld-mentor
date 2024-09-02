import streamlit as st
from streamlit_searchbox import st_searchbox

from app_ui_logic import (write_user_message, write_top_bar,
                          write_chat_message, init_login_session_state, init_app_session_state,
                          handle_user_prompt, render_login_page, render_reset_page, get_typeahead_suggestions_pickle)
from constants.constants import (APP_TITLE)
from log_config import get_logger

# Initialize logger
log = get_logger()

# App Execution Start
# Initialize Streamlit session state and style the app
main_page_component = st
if "init_session" not in st.session_state:
    main_page_component.session_state.init_session = False
main_page_component.set_page_config(page_title=APP_TITLE, page_icon="💻")
main_page_component.markdown("""
    <style>
        .block-container {
            padding-top: 32px;
            padding-bottom: 32px;
            padding-left: 0;
            padding-right: 0;
        }
        .element-container img {
            background-color: #000000;
        }
        .main-header {
            font-size: 24px;
            font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)

if not main_page_component.session_state.init_session:
    init_login_session_state(main_page_component)

try:
    if not main_page_component.session_state.is_authenticated:
        if main_page_component.session_state.login_page:
            render_login_page(main_page_component)
        else:
            render_reset_page(main_page_component)
    else:
        # Main app logic
        write_top_bar(main_page_component)
        # Render chat content on page rerun
        page_write_component = main_page_component.container()
        for question, answer in zip(st.session_state.questions, st.session_state.answers):
            write_user_message(question, page_write_component)
            write_chat_message(answer, page_write_component)
        col1, col2 = page_write_component.columns([10, 2])
        # Pass search function to search box
        with col1:
            st_searchbox(get_typeahead_suggestions_pickle, key="user_prompt",
                         label=("You are talking to an AI, "
                                "specially trained on helping you with "
                                "Low Level Software Designs."),
                         placeholder="Start learning LLD",
                         edit_after_submit="option")
        with col2:
            st.button("Submit", on_click=handle_user_prompt, args=(main_page_component, page_write_component),
                      type="primary")

    if not main_page_component.session_state.init_session:
        init_app_session_state(main_page_component)
        main_page_component.session_state.init_session = True
except Exception as e:
    log.error(f"Error found in the application: {str(e)}")
