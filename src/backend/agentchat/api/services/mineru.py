import os
import shutil
import tempfile
from pathlib import Path

import fitz
from loguru import logger
from magic_pdf.data.data_reader_writer import FileBasedDataReader
from magic_pdf.tools.cli import ms_office_suffixes, image_suffixes, pdf_suffixes
from magic_pdf.tools.common import do_parse
from magic_pdf.utils.office_to_pdf import convert_file_to_pdf


def convert_pdf_to_markdown(path, output_dir, method="auto", lang=None, debug_able=False, start_page_id=0, end_page_id=None):
    os.makedirs(output_dir, exist_ok=True)
    temp_dir = tempfile.mkdtemp()


    def read_fn(path: Path):
        if path.suffix in ms_office_suffixes:
            convert_file_to_pdf(str(path), temp_dir)
            fn = os.path.join(temp_dir, f"{path.stem}.pdf")
        elif path.suffix in image_suffixes:
            with open(str(path), 'rb') as f:
                bits = f.read()
            pdf_bytes = fitz.open(stream=bits).convert_to_pdf()
            fn = os.path.join(temp_dir, f"{path.stem}.pdf")
            with open(fn, 'wb') as f:
                f.write(pdf_bytes)
        elif path.suffix in pdf_suffixes:
            fn = str(path)
        else:
            raise Exception(f"Unknown file suffix: {path.suffix}")

        disk_rw = FileBasedDataReader(os.path.dirname(fn))
        return disk_rw.read(os.path.basename(fn))


    def parse_doc(doc_path: Path):
        try:
            file_name = str(Path(doc_path).stem)
            pdf_data = read_fn(doc_path)
            do_parse(
                output_dir,
                file_name,
                pdf_data,
                [],
                method,
                debug_able,
                start_page_id=start_page_id,
                end_page_id=end_page_id,
                lang=lang
            )

        except Exception as e:
            logger.exception(e)


    if os.path.isdir(path):
        for doc_path in Path(path).glob('*'):
            if doc_path.suffix in pdf_suffixes + image_suffixes + ms_office_suffixes:
                parse_doc(doc_path)
    else:
        parse_doc(Path(path))

    shutil.rmtree(temp_dir)


if __name__ == '__main__':
    convert_pdf_to_markdown()