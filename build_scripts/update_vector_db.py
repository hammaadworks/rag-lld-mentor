from constants.constants import EMBEDDING_MODEL, FAISS_STORE
from db_build import run_db_build
from extract_urls import extract_main


def main_def():
    extract_main()
    run_db_build()
    print(f"Success:\nModel: {EMBEDDING_MODEL}\nPKL files are stored in {FAISS_STORE}")


if __name__ == "__main__":
    main_def()
