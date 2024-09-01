# import os
# import sys
# import pandas as pd
#
# sys.path.append("..")
# # from pdfminer.utils import
# from langchain_community.document_loaders import UnstructuredImageLoader
# from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader
#
# df = pd.read_excel("111.xlsx")
# df.to_csv("112.csv")
#
# loader = CSVLoader("111.csv")
# data = loader.load_and_split()
#
# for item in data:
#     print(item)

from langchain_community.document_loaders import UnstructuredMarkdownLoader

loader = UnstructuredMarkdownLoader("MySQL.md")

data = loader.load_and_split()

print(data)