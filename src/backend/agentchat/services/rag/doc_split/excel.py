import os

import pandas as pd
from langchain_community.document_loaders import CSVLoader
from langchain_text_splitters import TextSplitter


def excel_loader(path: str, text_splitter: TextSplitter):
    csv_path = path.replace('xlsx', 'csv')
    df = pd.read_excel(path)
    df.to_csv(csv_path)

    loader = CSVLoader(csv_path, encoding='utf-8')

    # 删除CSV的缓存文件
    delete_cache_file(csv_path)
    result = loader.load_and_split(text_splitter=text_splitter)
    return result

def delete_cache_file(path: str):
    if os.path.exists(path):
        os.remove(path)


