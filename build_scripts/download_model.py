from langchain_community.embeddings import HuggingFaceBgeEmbeddings

from constants.constants import (EMBEDDING_MODEL)

model = HuggingFaceBgeEmbeddings(model_name=EMBEDDING_MODEL, model_kwargs={'device': 'cpu'})
