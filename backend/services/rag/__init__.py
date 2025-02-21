from services.rag.load_document import load_folder_all_file
from config.user_config import userConfig

def init_rag_data():
    input_dir = userConfig.RAG_INPUT_DIR

    load_folder_all_file(input_dir)