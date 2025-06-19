import os.path
import re
from datetime import datetime, timedelta
from uuid import uuid4
from agentchat.schema.chunk import ChunkModel

class MarkdownParser:
    def __init__(self, chunk_size=500, overlap_size=100):
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.header_pattern = r'^(#{1,5})\s+(.+)$'
        self.link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        self.img_pattern = r'!\[([^\]]+)\]\(([^)]+)\)'

    async def split_text_with_headers(self, text, header_path):
        """
        将文本切分成块，每块都包含完整的标题路径
        """
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + self.chunk_size

            # 检查链接和图片是否被切断
            if end < text_length:
                for pattern in [self.link_pattern, self.img_pattern]:
                    matches = list(re.finditer(pattern, text))
                    for match in matches:
                        if start < match.start() < end < match.end():
                            end = match.start()

                # 调整到句子边界
                while end > start and end < text_length and text[end] not in '.!?\n':
                    end += 1
                if end < text_length:
                    end += 1

            chunk_text = text[start:end].strip()
            if chunk_text:
                full_chunk = f"{header_path}\n\n{chunk_text}"
                chunks.append(full_chunk)

            # 更新起始位置，考虑重叠区域
            start = end - self.overlap_size

        return chunks

    async def parse_markdown_headers(self, text):
        """
        解析Markdown文件的标题结构，并按标题切分文本内容
        """
        current_headers = {i: '' for i in range(1, 6)}  # 1-5级标题
        chunks = []
        current_text = []

        lines = text.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            header_match = re.match(self.header_pattern, line)

            if header_match:
                # 遇到标题前先处理积累的文本
                if current_text:
                    full_text = '\n'.join(current_text)
                    header_path = ' > '.join([h for h in current_headers.values() if h])
                    chunks.extend(await self.split_text_with_headers(full_text, header_path))
                    current_text = []

                # 更新标题层级和标题文本
                level = len(header_match.group(1))  # # 的数量
                header_text = header_match.group(2)
                current_headers[level] = header_text

                # 清除当前层级之后的所有子标题
                for l in range(level + 1, 6):
                    current_headers[l] = ''

            else:
                # 收集普通文本
                current_text.append(line)

            i += 1

            # 如果是最后一行或者下一行是标题，处理积累的文本
            if i >= len(lines) or re.match(self.header_pattern, lines[i]):
                if current_text:
                    full_text = '\n'.join(current_text)
                    header_path = ' > '.join([h for h in current_headers.values() if h])
                    chunks.extend(await self.split_text_with_headers(full_text, header_path))
                    current_text = []

        # 处理最后剩余的文本
        if current_text:
            full_text = '\n'.join(current_text)
            header_path = ' > '.join([h for h in current_headers.values() if h])
            chunks.extend(await self.split_text_with_headers(full_text, header_path))

        return chunks

    async def parse_file(self, file_path):
        """
        读取指定文件并解析Markdown内容
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return text

    async def parse_into_chunks(self, file_id, file_path, knowledge_id):
        text = await self.parse_file(file_path)
        contents = await self.parse_markdown_headers(text)
        chunks = []
        update_time = datetime.utcnow() + timedelta(hours=8)
        for content in contents:
            chunks.append(ChunkModel(
                chunk_id=f"{os.path.splitext(file_path)}_{uuid4().hex}",
                content=content,
                file_id=file_id,
                file_name=os.path.basename(file_path),
                knowledge_id=knowledge_id,
                update_time=update_time
            ))

        return chunks

markdown_parser = MarkdownParser()