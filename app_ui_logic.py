import random
import string
import time
from datetime import datetime
from itertools import tee
from typing import List

import pytz
import streamlit as st
from thefuzz import process as fuzz_process

from constants.constants import (AI_ICON, USER_ICON, ASIA_KOLKATA, RESET_CODE_LENGTH, PASSWORD_LENGTH)
from constants.typeahead_constants import TYPEAHEAD_OPTIONS, TYPEAHEAD_OPTIONS_LIMIT
from log_config import get_logger
from misc_scripts.faiss_chat_openai import (chat_completion_request, run_chain, build_chain)
from model.LoginModel import UserModel
from util.MailUtil import send_reset_code_mail
from util.timelog import CodeTimer

# Initialize logger
log = get_logger()

import mapper.RpaMapper as rpaSink

EMAIL_ID = "Email"


def date_today():
    """Get current date and time in the specified timezone."""
    return datetime.now(pytz.timezone(ASIA_KOLKATA))


def init_login_session_state(page_component):
    if 'is_authenticated' not in st.session_state:
        page_component.session_state.is_authenticated = False
    if 'login_page' not in st.session_state:
        page_component.session_state.login_page = True
    if 'reset_full_page' not in st.session_state:
        page_component.session_state.reset_full_page = False
    if 'reset_code' not in st.session_state:
        page_component.session_state.reset_code = None
    if 'reset_email' not in st.session_state:
        page_component.session_state.reset_email = None
    if 'name' not in st.session_state:
        page_component.session_state.name = None
    if 'email' not in st.session_state:
        page_component.session_state.email = None


def init_app_session_state(page_component):
    """Initialize session state for Streamlit app."""
    with CodeTimer("init session"):
        log.info(f"Inside init_streamlit_session_state: {ASIA_KOLKATA=}")

        if "questions" not in st.session_state:
            page_component.session_state.questions = []
        if "answers" not in st.session_state:
            page_component.session_state.answers = []

        if 'llm_chain' not in st.session_state:
            page_component.session_state['llm_chain'] = build_chain()[0]


def clear_chat():
    """Clear chat session."""
    log.info("Inside clear_chat()")
    st.session_state.questions = []
    st.session_state.answers = []
    st.session_state.user_prompt["result"] = ""
    st.session_state.user_prompt["search"] = ""


def refresh_page():
    """Logout user session."""
    log.info("Inside refresh_page()")
    st.session_state.is_authenticated = False
    st.session_state.login_page = True
    st.session_state.reset_full_page = False
    st.session_state.reset_code = None
    st.session_state.reset_email = None
    st.session_state.name = None
    st.session_state.email = None


def write_top_bar(page_component):
    """Display top bar of the chat interface."""
    log.info("Inside write_top_bar()")
    _, col_1, col_2, col_3 = page_component.columns([1, 2, 6, 4])
    col_1.image(AI_ICON, use_column_width='always')
    col_2.header = "CS Agent Assistant"
    col_2.write(f"<h1 class='main-header'>{col_2.header}</h1>", unsafe_allow_html=True)
    col_2.caption(f"You are logged in as **{st.session_state.name}**. Refresh to Logout.")
    col_3.button("Logout User", on_click=refresh_page, type="primary")
    col_3.button("Clear Chat ", on_click=clear_chat)


def write_user_message(question_string, page_component):
    """Display user's message."""
    log.info(f"Inside write_user_message: {question_string=}")
    col_1, col_2 = page_component.columns([1, 12])
    col_1.image(USER_ICON, use_column_width='always')
    col_2.warning(question_string)


def render_answer(answer_string, page_component):
    """Render assistant's answer."""
    log.info(f"Inside render_answer: {answer_string=}")
    col_1, col_2 = page_component.columns([1, 12])
    col_1.image(AI_ICON, use_column_width='always')
    col_2.write(answer_string)


def render_stream_tool(write_stream, page_component):
    """Render stream of tool responses."""
    col_1, col_2 = page_component.columns([1, 12])
    col_1.image(AI_ICON, use_column_width='always')
    col_2.write_stream(chunk.content for chunk in write_stream)


def render_stream(write_stream, page_component):
    """Render stream of responses."""
    col_1, col_2 = page_component.columns([1, 12])
    col_1.image(AI_ICON, use_column_width='always')
    col_2.write_stream(chunk.get('answer').content for chunk in write_stream if 'answer' in chunk)


def render_sources(sources, page_component):
    """Render sources of information."""
    log.info(f"Inside render_sources: {sources=}")
    _, col_2 = page_component.columns([1, 12])
    with col_2.expander("Sources"):
        for source in sources:
            st.write(source)


def write_chat_message(md, page_component):
    """Write chat message to Streamlit interface."""
    log.info(f"Inside write_chat_message: {md=}")
    chat = page_component.container()
    with chat:
        with CodeTimer("render user answer"):
            render_answer(md['answer'], page_component)
            if md['sources']:
                render_sources(md['sources'], page_component)


def get_typeahead_suggestions_pickle(key: str):
    """Get typeahead suggestions using fuzzy matching."""
    options_list = []
    options = fuzz_process.extract(key, TYPEAHEAD_OPTIONS, limit=TYPEAHEAD_OPTIONS_LIMIT)
    for option in options:
        options_list.append(option[0])
    options_list.insert(0, key)
    return options_list


def search_box(key: str) -> List[any]:
    """Function with list of labels for the search box."""
    prev_query = st.session_state.prev_query

    if key.count(" ") == 0:
        st.session_state.prev_query = key
        st.session_state.prev_search = [key]
        return st.session_state.prev_search

    if key.count(" ") != prev_query.count(" ") or not key.startswith(prev_query):
        st.session_state.prev_query = key
        st.session_state.prev_search = get_typeahead_suggestions_pickle(key)
        st.session_state.prev_search.insert(0, key)
        return st.session_state.prev_search

    if key.startswith(prev_query):
        st.session_state.prev_query = key
        st.session_state.prev_search = st.session_state.prev_search[1:]
        st.session_state.prev_search.insert(0, key)
        return st.session_state.prev_search


def password_digester(password: str):
    # Enable for enhanced security
    # return hashlib.md5(password.encode('utf-8')).hexdigest()
    return password.strip()


def authenticate_user(user: UserModel, password: str):
    """Authenticate user."""
    try:
        return True if password_digester(password) == user.password else False
    except Exception as e:
        log.error(f"Error in app_ui_logic>> {str(e)}")


def login_user(page_component, user_email, user_password):
    user: UserModel = rpaSink.get_user_by_email(email=user_email)
    if not user.email:
        st.error("Invalid Email Id")
    elif not authenticate_user(user, user_password):
        st.error("Invalid Password")
    else:
        st.success("Login successful!")
        st.write("Routing to CSGPT application...")  # Replace with your main app code
        page_component.session_state.is_authenticated = True
        page_component.session_state.name = user.name
        page_component.session_state.email = user.email
        st.rerun()


def handle_user_prompt(main_component, write_component):
    """Handle user prompt submission."""
    log.info(f"Inside handle_user_prompt: {main_component.session_state.user_prompt=}")
    search_entry = main_component.session_state.user_prompt.get("search", None) or ""
    result_entry = main_component.session_state.user_prompt.get("result", None) or ""
    user_prompt_str = search_entry if len(search_entry) >= len(result_entry) else result_entry
    main_component.session_state.questions.append(user_prompt_str)

    messages = [
        {"role": "system", "content": "You are an object-oriented low level software designing Python expert."},
        {"role": "user", "content": user_prompt_str}
    ]

    chat_response = chat_completion_request(messages)
    assistant_message = chat_response.json()["choices"][0]["message"]
    messages.append(assistant_message)
    _answer = ""
    document_list = []

    llm_chain = main_component.session_state.llm_chain
    result = run_chain(llm_chain, user_prompt_str)
    write_stream, collect_stream = tee(result, 2)

    write_component.markdown("####")
    write_user_message(user_prompt_str, write_component)
    render_stream(write_stream, write_component)
    for chunk in collect_stream:
        if 'answer' in chunk:
            _answer += chunk.get('answer').content
        if 'docs' in chunk:
            document_list.extend(set([d.metadata['source'] for d in chunk['docs']]))

    main_component.session_state.answers.append({'answer': _answer, 'sources': document_list})
    logged_in_email = main_component.session_state.email
    try:
        rpaSink.save_chat(_answer, user_prompt_str, logged_in_email, date_today())
    except Exception as e:
        log.error(f"Error saving to DB: {str(e)}")
    finally:
        main_component.session_state.user_prompt["search"] = ""
        main_component.session_state.user_prompt["result"] = ""


def send_reset_code_email(user_email):
    choice_list = string.ascii_uppercase + string.digits[1:]
    reset_code = ''.join(random.choice(choice_list) for _ in range(RESET_CODE_LENGTH))
    send_reset_code_mail(user_email, reset_code)
    log.info(f"Sent mail to {user_email=} with {reset_code=}")
    return reset_code


def render_login_page(main_page_component):
    st.title("🔐 CSGPT Login Page")
    with st.form(key='login_form'):
        user_email = st.text_input(EMAIL_ID)
        user_password = st.text_input("Password", type='password')
        _, button_1, _, button_2, _ = st.columns(spec=[1, 2, 1, 2, 1], gap="medium")
        submit_button = button_1.form_submit_button(label='Login', type="primary")
        reset_password = button_2.form_submit_button(label='Reset Password')

    if submit_button:
        login_user(main_page_component, user_email, user_password)

    if reset_password:
        main_page_component.session_state.login_page = False
        main_page_component.rerun()


def render_reset_half_page(main_page_component):
    st.title("🔁 CSGPT Reset Password Page")
    reset_form = main_page_component.form(key='reset_form')
    user_email = reset_form.text_input(EMAIL_ID)
    _, button_1, _, button_2, _ = reset_form.columns(spec=[1, 2, 1, 2, 1], gap="medium")
    back_login = button_1.form_submit_button(label='Back')
    send_mail = button_2.form_submit_button(label='Next', type="primary")

    if back_login:
        refresh_page()
        st.rerun()

    if send_mail:
        user: UserModel = rpaSink.get_user_by_email(email=user_email)
        if not user.email:
            st.error(f"Invalid {EMAIL_ID}")
        else:
            reset_code = send_reset_code_email(user.email)
            log.info(f"Reset code for {user.email} is: {reset_code}")
            main_page_component.session_state.reset_email = user.email
            main_page_component.session_state.reset_code = reset_code
            main_page_component.session_state.reset_full_page = True
            st.success(f"Mail sent successfully to {user.email}")
            main_page_component.rerun()


def render_reset_full_page(main_page_component):
    st.title("🔁 CSGPT Reset Password Page")
    email = main_page_component.session_state.reset_email
    reset_code = main_page_component.session_state.reset_code

    reset_form = main_page_component.form(key='reset_form')
    _ = reset_form.text_input(EMAIL_ID, value=email, disabled=True)
    new_password = reset_form.text_input("New Password", type='password')
    confirm_password = reset_form.text_input("Confirm Password", type='password')
    user_reset_code = reset_form.text_input("Reset Code", placeholder=f'Reset code sent successfully to {email}')
    # reset_form.caption(f"[test] Reset code = {reset_code}, will be removed after email integration")
    _, button_1, _, button_2, _ = reset_form.columns(spec=[1, 2, 1, 2, 1], gap="medium")
    back_login = button_1.form_submit_button(label='Back to Login')
    reset_button = button_2.form_submit_button(label='Reset Password', type="primary")

    if back_login:
        refresh_page()
        st.rerun()

    if reset_button:
        if new_password == confirm_password and reset_code == user_reset_code and len(new_password) >= PASSWORD_LENGTH:
            password = password_digester(new_password)
            rpaSink.update_user_password(email, password)
            st.success("Password reset successfully!! 🎉🎉")
            time.sleep(2)
            refresh_page()
            st.rerun()

        else:
            if new_password != confirm_password:
                st.error("Passwords do not match")
            elif len(new_password) < PASSWORD_LENGTH:
                st.error(f"Passwords length must be greater or equal to {PASSWORD_LENGTH} characters")
            elif reset_code != user_reset_code:
                st.error("Invalid Reset Code")
            else:
                st.error("Unable to change passwords, try after  sometime")


def render_reset_page(main_page_component):
    if not main_page_component.session_state.reset_full_page:
        render_reset_half_page(main_page_component)
    else:
        render_reset_full_page(main_page_component)
