import os
import sys
import platform
from loguru import logger

def convert_to_pdf(input_path):
    if not os.path.exists(input_path):
        raise ValueError(f"文件不存在: {input_path}")

    filename, ext = os.path.splitext(input_path)
    output_path = filename + ".pdf"

    system = platform.system()

    try:
        if system == "Windows":
            # 使用 comtypes 调用 Office（仅限 Windows）
            import comtypes.client

            if ext.lower() == ".docx":
                word = comtypes.client.CreateObject("Word.Application")
                doc = word.Documents.Open(input_path)
                doc.ExportAsFixedFormat(
                    OutputFileName=output_path,
                    ExportFormat=0,  # wdExportFormatPDF
                    OpenAfterExport=False,
                    OptimizeFor=0,  # wdExportOptimizeForPrint
                    CreateBookmarks=1,  # wdExportCreateHeadingBookmarks
                )
                doc.Close()
                word.Quit()
                logger.info(f"已转换为 PDF: {output_path}")

            elif ext.lower() == ".pptx":
                powerpoint = comtypes.client.CreateObject("Powerpoint.Application")
                presentation = powerpoint.Presentations.Open(input_path)
                presentation.SaveAs(output_path, 32)  # 32 表示 PDF 格式
                presentation.Close()
                powerpoint.Quit()
                logger.info(f"已转换为 PDF: {output_path}")
            else:
                raise ValueError("不支持的文件类型")
            return output_path
        elif system == "Linux" or "Darwin":  # Mac 或者 Linux
            # 使用 unoconv（基于 LibreOffice）
            import unoconv
            unoconv.convert(input_path, output_path, format="pdf")
            logger.info(f"已转换为 PDF: {output_path}")
            return output_path
        else:
            raise ValueError(f"不支持的操作系统: {system}")


    except Exception as e:
        raise ValueError(f"转换失败: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("请提供一个要转换的文件路径。")
        logger.info("示例: python convert_to_pdf.py example.docx")
        sys.exit(1)

    file_path = sys.argv[1]
    convert_to_pdf(file_path)