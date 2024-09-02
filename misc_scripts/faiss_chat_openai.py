import os
from operator import itemgetter

import requests
from langchain.globals import set_llm_cache
from langchain.memory import ConversationBufferMemory
from langchain_community.cache import InMemoryCache
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.messages import get_buffer_string
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    format_document,
)
from langchain_core.prompts.prompt import PromptTemplate
from langchain_core.runnables import (
    RunnableLambda,
    RunnablePassthrough,
)
from langchain_openai.chat_models import ChatOpenAI

from constants.constants import (EMBEDDING_MODEL, FAISS_STORE, STANDALONE_PROMPT_TEMPLATE, GPT_3_5_TURBO, GPT_4)


def chat_completion_request(input_prompt):
    model = GPT_4
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + os.environ['OPENAI_API_KEY'],
    }

    json_data = {"model": model, "messages": input_prompt}

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=json_data,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e


def init_caching():
    set_llm_cache(InMemoryCache())
    # set_llm_cache(SQLiteCache(database_path="analytics/langchain.db"))


def build_chain():
    llm_final_response = ChatOpenAI(model_name=GPT_4, temperature=0.0, max_tokens=1500)
    llm_intermediate_steps = ChatOpenAI(model_name=GPT_3_5_TURBO, temperature=0.0, max_tokens=1500)
    embeddings = HuggingFaceBgeEmbeddings(model_name=EMBEDDING_MODEL, model_kwargs={'device': 'cpu'})
    vectorstore = FAISS.load_local(FAISS_STORE, embeddings, allow_dangerous_deserialization=True)
    retriever = vectorstore.as_retriever(search_kwargs={'k': 2})
    CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(STANDALONE_PROMPT_TEMPLATE)
    template = """Answer the question based only on the following context:
    {context}

    Question: {question}
    """
    ANSWER_PROMPT = ChatPromptTemplate.from_template(template)
    DEFAULT_DOCUMENT_PROMPT = PromptTemplate.from_template(template="{page_content}")

    def _combine_documents(docs, document_prompt=DEFAULT_DOCUMENT_PROMPT, document_separator="\n\n"):
        doc_strings = [format_document(doc, document_prompt) for doc in docs]
        return document_separator.join(doc_strings)

    standalone_question = \
        {"standalone_question":
             {"question": lambda x: x["question"], "chat_history": lambda x: get_buffer_string(x["chat_history"])}
             | CONDENSE_QUESTION_PROMPT | llm_intermediate_steps | StrOutputParser()}

    memory = ConversationBufferMemory(
        return_messages=True, output_key="answer", input_key="question"
    )

    loaded_memory = RunnablePassthrough.assign(
        chat_history=RunnableLambda(memory.load_memory_variables) | itemgetter("history"),
    )

    retrieved_documents = {
        "docs": itemgetter("standalone_question") | retriever,
        "question": lambda x: x["standalone_question"],
    }

    final_inputs = {
        "context": lambda x: _combine_documents(x["docs"]),
        "question": itemgetter("question"),
    }

    answer = {
        "answer": final_inputs | ANSWER_PROMPT | llm_final_response,
        "docs": itemgetter("docs"),
    }

    final_chain = loaded_memory | standalone_question | retrieved_documents | answer

    return final_chain, memory


def run_chain(chain, prompt: str):
    init_caching()
    inputs = {
        "question": prompt
    }
    return chain.stream(inputs)
