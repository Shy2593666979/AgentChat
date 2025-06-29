from docling.document_converter import DocumentConverter

source = "C:\\Users\\枯木逢春i\\Desktop\\test_pdf.pdf"  # document per local path or URL
converter = DocumentConverter()
result = converter.convert(source)
print(result.document.export_to_markdown())  # output: "## Docling Technical Report[...]"