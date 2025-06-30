

from docx import Document
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def convert_docx_to_pdf(input_docx, output_pdf):
    # 读取Word文档
    doc = Document(input_docx)

    # 创建PDF
    c = canvas.Canvas(output_pdf, pagesize=letter)
    width, height = letter

    # 设置字体（使用中文时需要）
    pdfmetrics.registerFont(TTFont('SimSun', 'SimSun.ttf'))
    c.setFont('SimSun', 12)

    y = height - 40  # 起始位置

    # 逐段落写入
    for para in doc.paragraphs:
        if y < 40:  # 如果页面空间不足，创建新页面
            c.showPage()
            y = height - 40

        text = para.text
        c.drawString(40, y, text)
        y -= 20  # 行间距

    c.save()


# 使用示例
convert_docx_to_pdf(r"C:\Users\harry\Desktop\数据\其他\纪律管理规定.docx", 'output.pdf')

