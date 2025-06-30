import pymupdf4llm
import pathlib

pdf_file = r"C:\Users\harry\Desktop\数据\其他\2023商保福利介绍-公司付费方案.pdf"
# md_text = pymupdf4llm.to_markdown("C:\\Users\\枯木逢春i\\Desktop\\test_pdf.pdf")
# print(md_text)




# 支持逐字提取和结构分析：
md_text_words = pymupdf4llm.to_markdown(
    doc=pdf_file,
    write_images=True,
    image_path="images",
    image_format="png",
    dpi=300
)

output_file = pathlib.Path("output.md")
output_file.write_bytes(md_text_words.encode())
print(md_text_words)

"""
|姓名|学号|班级|性别|手机号|
|---|---|---|---|---|
|田明广|212889331|2024.1|男|1993930601211258|
|田明广|212889331|2024.1|男|1993930212115608|
|田明广|212889331|2024.1|男|1993930631698158|
|田明广|212889331|2024.1|女|1993930621215048|

# 第一段

查看 Docling [的文档，了解有关安装、使用、概念、配方、扩展等的详细信息。](https://docling-project.github.io/docling/)
# 第二段

[通过我们的示例进行实际操作，演示如何使用 Docling 解决不同的应用程序用例。](https://docling-project.github.io/docling/examples/)      
## 集成

[为了进一步加速您的 AI 应用程序开发，请查看 Docling 与流行框架和工具的本机集成。](https://docling-project.github.io/docling/integrations/)

"""
