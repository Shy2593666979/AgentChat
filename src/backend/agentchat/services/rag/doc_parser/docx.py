from agentchat.services.rag.doc_parser.pdf import pdf_parser
from agentchat.services.transform_paper.convert_pdf import convert_to_pdf


class DocxParser:
    def __init__(self):
        pass

    async def convert_pdf(self, file_path: str):
        return convert_to_pdf(file_path)

    async def parse_into_chunks(self, file_id, file_path, knowledge_id):
        pdf_file_path = await self.convert_pdf(file_path)
        return await pdf_parser.parse_into_chunks(file_id, pdf_file_path, knowledge_id)


docx_parser = DocxParser()

# def word_loader(path: str, text_splitter: TextSplitter):
#     loader = UnstructuredWordDocumentLoader(path)
#
#     result = loader.load_and_split(text_splitter=text_splitter)
#     return result
# def word_loader(path: str, text_splitter: TextSplitter):
#     # 使用 python-docx 加载 Word 文档
#     doc = Document(path)
#     # 读取文档内容
#     pages = [p.text for p in doc.paragraphs]
#     result = text_splitter.split_documents(pages)
#     return result

# from docx import Document
# from reportlab.pdfgen import canvas
# from reportlab.lib.pagesizes import letter
# from reportlab.pdfbase import pdfmetrics
# from reportlab.pdfbase.ttfonts import TTFont
#
#
# def convert_docx_to_pdf(input_docx, output_pdf):
#     # 读取Word文档
#     doc = Document(input_docx)
#
#     # 创建PDF
#     c = canvas.Canvas(output_pdf, pagesize=letter)
#     width, height = letter
#
#     # 设置字体（使用中文时需要）
#     pdfmetrics.registerFont(TTFont('SimSun', 'SimSun.ttf'))
#     c.setFont('SimSun', 12)
#
#     y = height - 40  # 起始位置
#
#     # 逐段落写入
#     for para in doc.paragraphs:
#         if y < 40:  # 如果页面空间不足，创建新页面
#             c.showPage()
#             y = height - 40
#
#         text = para.text
#         c.drawString(40, y, text)
#         y -= 20  # 行间距
#
#     c.save()


