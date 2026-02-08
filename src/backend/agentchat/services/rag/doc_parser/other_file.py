import os
import csv
import json
import shutil
import tempfile
from bs4 import BeautifulSoup


async def other_file_to_txt(file_path: str) -> str:
    """
    各种文本类文件 → txt
    """
    suffix = os.path.splitext(file_path)[1].lower()

    # 已经是 txt，直接返回
    if suffix == ".txt":
        return file_path

    fd, txt_path = tempfile.mkstemp(suffix=".txt")
    os.close(fd)

    # JSON
    if suffix == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        with open(txt_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # HTML
    elif suffix in {".html", ".htm"}:
        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        text = soup.get_text(separator="\n", strip=True)

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)

    # CSV
    elif suffix == ".csv":
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)

        with open(txt_path, "w", encoding="utf-8") as f:
            for row in rows:
                f.write("\t".join(row) + "\n")

    # 其他：当普通文本
    else:
        shutil.copyfile(file_path, txt_path)

    return txt_path
