from rag.load_document import load_folder_all_file
from config import user_config

def init_rag_data():
    input_dir = user_config.RAG_INPUT_DIR

    load_folder_all_file(input_dir)