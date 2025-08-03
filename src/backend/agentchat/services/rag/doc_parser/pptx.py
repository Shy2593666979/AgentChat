from agentchat.services.rag.doc_parser.pdf import pdf_parser
from agentchat.services.transform_paper.convert_pdf import convert_to_pdf


class PPTXParser:
    def __init__(self):
        pass

    async def convert_pdf(self, file_path: str):
        return convert_to_pdf(file_path)

    async def parse_into_chunks(self, file_id, file_path, knowledge_id):
        pdf_file_path = await self.convert_pdf(file_path)
        return await pdf_parser.parse_into_chunks(file_id, pdf_file_path, knowledge_id)

pptx_parser = PPTXParser()