import os
import tempfile

from loguru import logger
import pypandoc


def md_text_to_docx(md_text, output_path=None):
    """
    将Markdown文本直接转换为DOCX文件

    参数:
        md_text: 包含Markdown格式的文本内容
        output_path: 输出的DOCX文件路径
    """
    if not output_path or not os.path.isdir(output_path):
        output_path = tempfile.mktemp()
    output_file_path = os.path.join(output_path, "ai_news.docx")
    try:
        # 直接将Markdown文本转换为DOCX
        # format='markdown' 指定输入格式
        # to='docx' 指定输出格式
        # output file 指定输出文件路径
        pypandoc.convert_text(
            source=md_text,
            to='docx',
            format='markdown',
            outputfile=output_file_path
        )
        logger.info(f"转换成功，文件已保存至: {output_file_path}")
        return output_file_path
    except Exception as e:
        logger.error(f"转换失败: {str(e)}")
        raise ValueError(f"转换失败: {str(e)}")