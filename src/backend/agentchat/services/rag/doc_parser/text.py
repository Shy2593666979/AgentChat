import os
from uuid import uuid4
from datetime import datetime, timedelta

from agentchat.schema.chunk import ChunkModel
from agentchat.settings import app_settings

class TextParser:
    def __init__(self):
        self.chunk_size = app_settings.rag.split.get('chunk_size')
        self.overlap_size = app_settings.rag.split.get('overlap_size')

    async def split_text_into_chunks_by_lines(self, text):
        """
        按换行符切割文本，确保每个 chunk 的大小不超过 chunk_size，并保留 overlap_size 的重叠部分。

        参数:
            text (str): 输入的文本。
            chunk_size (int): 每个 chunk 的最大字符数（默认500）。
            overlap_size (int): chunks 之间的重叠字符数（默认100），需小于 chunk_size。

        返回:
            list: 包含按行切割的 chunks 列表。
        """
        # 按换行符分割文本
        lines = text.splitlines()
        chunks = []
        current_chunk = []
        current_length = 0

        for line in lines:
            line_length = len(line)

            # 如果当前 chunk 加上新行超过 chunk_size，则保存当前 chunk
            if current_length + line_length > self.chunk_size:
                if current_chunk:
                    chunk = "\n".join(current_chunk)
                    chunks.append(chunk)
                    # 保留重叠部分：从当前 chunk 末尾截取 overlap_size 个字符
                    overlap = chunk[-self.overlap_size:] if self.overlap_size > 0 else ""
                    current_chunk = [overlap] if overlap else []
                    current_length = len(overlap)

            # 添加行到当前 chunk
            current_chunk.append(line)
            current_length += line_length

        # 处理最后一个 chunk
        if current_chunk:
            chunk = "\n".join(current_chunk)
            chunks.append(chunk)

        return chunks

    async def parse_file(self, file_path):
        """
        读取指定文件并解析Markdown内容
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            return text
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    async def parse_into_chunks(self, file_id, file_path, knowledge_id):
        file_content = await self.parse_file(file_path)
        contents = await self.split_text_into_chunks_by_lines(file_content)
        chunks = []
        update_time = datetime.utcnow() + timedelta(hours=8)
        for content in contents:
            chunk_id = f"{os.path.basename(file_path).split('_')[0]}_{uuid4().hex}"
            chunks.append(ChunkModel(
                chunk_id=chunk_id[:128] if len(chunk_id) > 128 else chunk_id,
                content=content,
                file_id=file_id,
                file_name=os.path.basename(file_path),
                knowledge_id=knowledge_id,
                update_time=update_time.isoformat()
            ))

        return chunks

text_parser = TextParser()
