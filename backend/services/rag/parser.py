import os
from services.rag.doc_split.text import text_parser
from services.rag.doc_split.markdown import markdown_parser

class DocParser:

    @classmethod
    async def parse_doc_into_chunks(cls, file_id, file_path, knowledge_id):
        file_suffix = file_path.split('.')[-1]
        chunks = []
        if file_suffix == 'md':
            chunks = await markdown_parser.parse_into_chunks(file_id, file_path, knowledge_id)
        elif file_suffix == 'txt':
            chunks = await text_parser.parse_into_chunks(file_id, file_path, knowledge_id)
        """其他文档"""
        return chunks

doc_parser = DocParser()