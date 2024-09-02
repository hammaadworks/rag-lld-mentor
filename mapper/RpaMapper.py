# Import necessary libraries
from typing import List

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from constants.constants import (CREATE_CHAT_TABLE_SQL, CREATE_LOGIN_TABLE_SQL, DEFAULT_LOGIN_TABLE_SQL)
from log_config import get_logger
from mapper.RpaDbConfig import config as sink_db
from model.LoginModel import UserModel

# Configure logging
log = get_logger()

# Create database engine connections
sink_engine = create_engine(sink_db.DATABASE_URI)
with Session(sink_engine) as session:
    session.execute(text(CREATE_LOGIN_TABLE_SQL))
    session.execute(text(CREATE_CHAT_TABLE_SQL))
    session.execute(text(DEFAULT_LOGIN_TABLE_SQL))
    session.commit()
# Log information about the database connections
log.info(f"Creating Sink DB Connection with {sink_db.__class__}")

DATE_STRING_CONDITION = "WHERE date(created_at) = :date_string"


def execute_query(query: str):
    """
    Executes a general SQL query on the sink database.

    Args:
        query: SQL query to execute.
    """
    try:
        with Session(sink_engine) as sink_session:
            log.info(f"In execute_query query>> {query}")
            response = sink_session.execute(text(query))
            sink_session.commit()
            return response
    except Exception as e:
        log.error(f"Exception in execute_query>> {str(e)}")
        raise IOError(f"Exception in execute_query: {str(e)}")


def make_batches(huge_list, batch_size):
    """
    Generates batches from a given list.

    Parameters:
    - huge_list (list): The list to be batched.
    - batch_size (int): The size of each batch.

    Yields:
    - list: A batch of elements from the original list.
    """
    total_size = len(huge_list)
    for batch_start in range(0, total_size, batch_size):
        yield huge_list[batch_start:min(batch_start + batch_size, total_size)]


def sanity_null_check(dict_list: list):
    """
    Replaces None or 'null' values in dictionaries within a list with an empty string.

    Args:
        dict_list: List of dictionaries to perform null value replacement.

    Returns:
        The modified list of dictionaries.
    """
    for dict_item in dict_list:
        for key in dict_item:
            if dict_item[key] is None or dict_item[key] == 'null':
                dict_item[key] = ''
    return dict_list


def list_sanity_null_check(row_list: list):
    """
    Replaces None or 'null' values in a list with an empty string.

    Args:
        row_list: List to perform null value replacement.

    Returns:
        The modified list.
    """
    return [item if (item is not None or 'null') else '' for item in row_list]


def execute_query_response(query: str):
    """
    Executes a general SQL query on the sink database.

    Args:
        query: SQL query to execute.
    """
    try:
        with Session(sink_engine) as sink_session:
            log.info(f"In execute_query query>> {query}")
            response = sink_session.execute(text(query)).fetchall()
            return response
    except Exception as e:
        log.error(f"Exception in execute_query>> {str(e)}")
        raise IOError(f"Exception in execute_query: {str(e)}")


def execute_query_column_response(query: str):
    """
    Executes a general SQL query on the sink database.

    Args:
        query: SQL query to execute.
    """
    try:
        with Session(sink_engine) as sink_session:
            log.info(f"In execute_query_column_response query>> {query}")
            response = sink_session.execute(text(query)).keys()
            return list(response)
    except Exception as e:
        log.error(f"Exception in execute_query_column_response>> {str(e)}")
        raise IOError(f"Exception in execute_query_column_response: {str(e)}")


def count_query(query: str):
    """
    Executes a SQL count query on the sink database.

    Args:
        query: SQL count query to execute.

    Returns:
        The count result.
    """
    try:
        with Session(sink_engine) as sink_session:
            log.info(f"In count_query query>> {query}")
            count = sink_session.execute(text(query)).fetchone()[0]
            log.debug(count)
            return count
    except Exception as e:
        log.error(f"Exception in count_query>> {str(e)}")
        raise IOError(f"Exception in count_query: {str(e)}")


def save_chat(result, prompt, email, date):
    """
    Save user chat
    """
    try:
        result = str(result)
        prompt = str(prompt)
        email = str(email)
        date = str(date)
        with Session(sink_engine) as sink_session:
            table_stmt = """INSERT INTO chat_history(email, question, answer, date) 
            VALUES (:email,:prompt,:result,:date);"""
            log.info(f"In save_chat query>> {table_stmt}")
            sink_session.execute(text(table_stmt).bindparams(email=email, prompt=prompt, result=result, date=date))
            sink_session.commit()
    except Exception as e:
        log.error(f"Exception in save_chat>> {str(e)}")
        raise IOError(f"Exception in save_chat: {str(e)}")


def get_typeahead_suggestions(key: str) -> List[str]:
    """
    Save user chat
    """
    try:
        with Session(sink_engine) as sink_session:
            table_stmt = """SELECT suggestions FROM typeahead t WHERE MATCH(suggestions) AGAINST(:key) limit 5;"""
            log.info(f"In get_typeahead_suggestions query>> {table_stmt}")
            result = sink_session.execute(text(table_stmt).bindparams(key=key)).fetchall()
            result = [r[0] for r in result]
            return result if result else []
    except Exception as e:
        log.error(f"Exception in save_chat>> {str(e)}")
        raise IOError(f"Exception in save_chat: {str(e)}")


def get_user_by_email(email: str) -> UserModel:
    """
    Get user details by Email
    """
    try:
        with Session(sink_engine) as sink_session:
            table_stmt = """SELECT * FROM login_details WHERE email=:email;"""
            log.info(f"In get_user_by_email query>> {table_stmt}")
            result = sink_session.execute(text(table_stmt).bindparams(email=email)).fetchone()
            if not result:
                return UserModel(name=None,
                                 email=None,
                                 password=None)
            result_key_index = result._key_to_index
            user = UserModel(name=result[result_key_index.get('name')],
                             email=result[result_key_index.get('email')],
                             password=result[result_key_index.get('password')])
            return user
    except Exception as e:
        log.error(f"Exception in get_user_by_email>> {str(e)}")
        raise IOError(f"Exception in get_user_by_email: {str(e)}")


def update_user_password(email, password):
    """
    Update User Password
    """
    try:
        with Session(sink_engine) as sink_session:
            table_stmt = """UPDATE login_details SET password=:password WHERE email=:email"""
            log.info(f"In update_user_password query>> {table_stmt}")
            sink_session.execute(text(table_stmt).bindparams(email=email, password=password))
            sink_session.commit()
    except Exception as e:
        log.error(f"Exception in update_user_password>> {str(e)}")
        raise IOError(f"Exception in update_user_password: {str(e)}")
