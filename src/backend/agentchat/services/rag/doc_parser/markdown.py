import os.path
import re
from datetime import datetime, timedelta
from uuid import uuid4
from agentchat.schema.chunk import ChunkModel


class MarkdownParser:
    def __init__(self, min_chunk_size=256, max_chunk_size=512, overlap_size=128):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        self.header_pattern = r'^(#{1,5})\s+(.+)$'
        self.link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        self.img_pattern = r'!\[([^\]]+)\]\(([^)]+)\)'

    def find_link_boundaries(self, text):
        """找到文本中所有链接和图片的边界位置"""
        boundaries = []
        for pattern in [self.link_pattern, self.img_pattern]:
            for match in re.finditer(pattern, text):
                boundaries.append((match.start(), match.end()))
        return boundaries

    def is_safe_cut_position(self, text, position, boundaries):
        """检查指定位置是否可以安全切割（不会切断链接）"""
        for start, end in boundaries:
            if start < position < end:
                return False
        return True

    def find_best_cut_position(self, text, target_position, boundaries):
        """找到最佳的切割位置，优先考虑句子边界"""
        # 首先检查目标位置是否安全
        if self.is_safe_cut_position(text, target_position, boundaries):
            # 向后查找句子边界
            for i in range(target_position, min(len(text), target_position + 50)):
                if text[i] in '.!?\n' and self.is_safe_cut_position(text, i + 1, boundaries):
                    return i + 1

        # 如果没找到合适的句子边界，向前查找安全位置
        for i in range(target_position, max(0, target_position - 100), -1):
            if self.is_safe_cut_position(text, i, boundaries):
                # 尝试找到句子边界
                for j in range(i, max(0, i - 50), -1):
                    if text[j] in '.!?\n' and self.is_safe_cut_position(text, j + 1, boundaries):
                        return j + 1
                return i

        return target_position

    async def split_text_with_headers(self, text, header_path):
        """
        将文本切分成块，每块都包含完整的标题路径，长度控制在300-512字符之间
        """
        chunks = []

        # 预留给header_path和格式字符的空间
        header_overhead = len(header_path) + 4  # "\n\n" + 一些缓冲

        # 如果header路径太长，截断它（保留最后几级标题）
        if header_overhead > 200:  # 给header更合理的空间限制
            header_parts = header_path.split(' > ')
            while len(' > '.join(header_parts)) + 4 > 200 and len(header_parts) > 1:
                header_parts = header_parts[1:]  # 移除第一级标题
            header_path = ' > '.join(header_parts)
            header_overhead = len(header_path) + 4

        # 按段落分割文本
        paragraphs = text.split('\n\n')
        current_chunk_text = ""

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # 检查添加当前段落后是否会超过最大长度
            test_text = current_chunk_text + ('\n\n' if current_chunk_text else '') + paragraph
            full_test_chunk = f"{header_path}\n\n{test_text}"

            if len(full_test_chunk) <= 1024:  # 总长度限制
                current_chunk_text = test_text

                # 检查是否达到最小长度要求
                if len(full_test_chunk) >= self.min_chunk_size + header_overhead:
                    # 如果超过最大长度，需要切割
                    if len(full_test_chunk) > self.max_chunk_size + header_overhead:
                        # 回退到上一个状态，处理当前积累的文本
                        prev_text = current_chunk_text.rsplit('\n\n' + paragraph, 1)[
                            0] if '\n\n' + paragraph in current_chunk_text else ""
                        if prev_text:
                            full_chunk = f"{header_path}\n\n{prev_text}"
                            if len(full_chunk) >= self.min_chunk_size:
                                chunks.append(full_chunk)

                        # 处理当前段落
                        current_chunk_text = paragraph
                    # 如果长度合适，继续积累
                    elif len(full_test_chunk) >= self.min_chunk_size:
                        # 可以作为一个chunk输出，但继续看是否能加更多内容
                        pass
            else:
                # 先处理之前积累的文本
                if current_chunk_text:
                    full_chunk = f"{header_path}\n\n{current_chunk_text}"
                    if len(full_chunk) >= self.min_chunk_size:
                        chunks.append(full_chunk)

                # 处理当前段落（可能需要进一步分割）
                current_chunk_text = paragraph
                full_chunk = f"{header_path}\n\n{current_chunk_text}"

                # 如果单个段落就超过最大长度，需要进一步分割
                if len(full_chunk) > self.max_chunk_size + header_overhead:
                    chunks.extend(await self.split_long_paragraph(paragraph, header_path))
                    current_chunk_text = ""
                elif len(full_chunk) >= self.min_chunk_size:
                    # 段落长度合适，作为新的起始
                    pass
                else:
                    # 段落太短，继续积累
                    pass

        # 处理最后剩余的文本
        if current_chunk_text:
            full_chunk = f"{header_path}\n\n{current_chunk_text}"
            if len(full_chunk) >= self.min_chunk_size:
                chunks.append(full_chunk)
            elif chunks:
                # 如果最后一块太短，尝试合并到前一块
                last_chunk = chunks[-1]
                combined = last_chunk + '\n\n' + current_chunk_text
                if len(combined) <= 1024:
                    chunks[-1] = combined
                else:
                    # 如果合并后太长，单独作为一块（即使较短）
                    chunks.append(full_chunk)
            else:
                # 如果这是唯一的chunk，即使短也要保留
                chunks.append(full_chunk)

        return chunks

    async def split_long_paragraph(self, paragraph, header_path):
        """分割过长的段落"""
        chunks = []
        header_overhead = len(header_path) + 4
        max_text_size = self.max_chunk_size - header_overhead
        boundaries = self.find_link_boundaries(paragraph)

        start = 0
        while start < len(paragraph):
            end = start + max_text_size

            if end >= len(paragraph):
                # 最后一段
                chunk_text = paragraph[start:].strip()
                if chunk_text:
                    full_chunk = f"{header_path}\n\n{chunk_text}"
                    chunks.append(full_chunk)
                break

            # 找到最佳切割位置
            end = self.find_best_cut_position(paragraph, end, boundaries)

            chunk_text = paragraph[start:end].strip()
            if chunk_text:
                full_chunk = f"{header_path}\n\n{chunk_text}"
                chunks.append(full_chunk)

            start = end - self.overlap_size if end > self.overlap_size else end

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
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            return text
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    async def parse_into_chunks(self, file_id: str, file_path: str, knowledge_id: str):
        text = await self.parse_file(file_path)
        contents = await self.parse_markdown_headers(text)
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


markdown_parser = MarkdownParser()
# import os.path
# import re
# from datetime import datetime, timedelta
# from uuid import uuid4
# from agentchat.schema.chunk import ChunkModel
#
#
# class MarkdownParser:
#     def __init__(self, chunk_size=512, overlap_size=128):  # 更小的chunk_size和overlap_size
#         self.chunk_size = chunk_size
#         self.overlap_size = overlap_size
#         self.header_pattern = r'^(#{1,5})\s+(.+)$'
#         self.link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
#         self.img_pattern = r'!\[([^\]]+)\]\(([^)]+)\)'
#
#     async def split_text_with_headers(self, text, header_path):
#         """
#         将文本切分成块，每块都包含完整的标题路径
#         """
#         chunks = []
#         start = 0
#         text_length = len(text)
#
#         # 预留给header_path和格式字符的空间
#         header_overhead = len(header_path) + 2  # "\n\n"
#
#         # 如果header路径太长，截断它（保留最后几级标题）
#         if header_overhead > 512:  # 如果header太长
#             header_parts = header_path.split(' > ')
#             while len(' > '.join(header_parts)) + 2 > 512 and len(header_parts) > 1:
#                 header_parts = header_parts[1:]  # 移除第一级标题
#             header_path = ' > '.join(header_parts)
#             header_overhead = len(header_path) + 2
#
#         max_text_size = 1024 - header_overhead
#         effective_chunk_size = min(self.chunk_size, max_text_size)
#
#         while start < text_length:
#             end = start + effective_chunk_size
#
#             # 检查链接和图片是否被切断
#             if end < text_length:
#                 for pattern in [self.link_pattern, self.img_pattern]:
#                     matches = list(re.finditer(pattern, text))
#                     for match in matches:
#                         if start < match.start() < end < match.end():
#                             end = match.start()
#
#                 # 调整到句子边界
#                 while end > start and end < text_length and text[end] not in '.!?\n':
#                     end += 1
#                 if end < text_length:
#                     end += 1
#
#             chunk_text = text[start:end].strip()
#             if chunk_text:
#                 full_chunk = f"{header_path}\n\n{chunk_text}"
#
#                 # 最终安全检查：确保绝对不超过1024字符
#                 if len(full_chunk) > 1024:
#                     max_chunk_text_len = 1024 - header_overhead - 10  # 留10字符缓冲
#                     chunk_text = chunk_text[:max_chunk_text_len].strip()
#                     full_chunk = f"{header_path}\n\n{chunk_text}"
#
#                 chunks.append(full_chunk)
#
#             # 更新起始位置，考虑重叠区域
#             start = end - self.overlap_size
#
#         return chunks
#
#     async def parse_markdown_headers(self, text):
#         """
#         解析Markdown文件的标题结构，并按标题切分文本内容
#         """
#         current_headers = {i: '' for i in range(1, 6)}  # 1-5级标题
#         chunks = []
#         current_text = []
#
#         lines = text.split('\n')
#         i = 0
#         while i < len(lines):
#             line = lines[i]
#             header_match = re.match(self.header_pattern, line)
#
#             if header_match:
#                 # 遇到标题前先处理积累的文本
#                 if current_text:
#                     full_text = '\n'.join(current_text)
#                     header_path = ' > '.join([h for h in current_headers.values() if h])
#                     chunks.extend(await self.split_text_with_headers(full_text, header_path))
#                     current_text = []
#
#                 # 更新标题层级和标题文本
#                 level = len(header_match.group(1))  # # 的数量
#                 header_text = header_match.group(2)
#                 current_headers[level] = header_text
#
#                 # 清除当前层级之后的所有子标题
#                 for l in range(level + 1, 6):
#                     current_headers[l] = ''
#
#             else:
#                 # 收集普通文本
#                 current_text.append(line)
#
#             i += 1
#
#             # 如果是最后一行或者下一行是标题，处理积累的文本
#             if i >= len(lines) or re.match(self.header_pattern, lines[i]):
#                 if current_text:
#                     full_text = '\n'.join(current_text)
#                     header_path = ' > '.join([h for h in current_headers.values() if h])
#                     chunks.extend(await self.split_text_with_headers(full_text, header_path))
#                     current_text = []
#
#         # 处理最后剩余的文本
#         if current_text:
#             full_text = '\n'.join(current_text)
#             header_path = ' > '.join([h for h in current_headers.values() if h])
#             chunks.extend(await self.split_text_with_headers(full_text, header_path))
#
#         return chunks
#
#     async def parse_file(self, file_path):
#         """
#         读取指定文件并解析Markdown内容
#         """
#         with open(file_path, 'r', encoding='utf-8') as f:
#             text = f.read()
#         return text
#
#     async def parse_into_chunks(self, file_id: str, file_path: str, knowledge_id: str):
#         text = await self.parse_file(file_path)
#         contents = await self.parse_markdown_headers(text)
#         chunks = []
#         update_time = datetime.utcnow() + timedelta(hours=8)
#         for content in contents:
#             chunk_id = f"{os.path.basename(file_path).split("_")[0]}_{uuid4().hex}"
#             chunks.append(ChunkModel(
#                 chunk_id=chunk_id[:128] if len(chunk_id) > 128 else chunk_id,
#                 content=content,
#                 file_id=file_id,
#                 file_name=os.path.basename(file_path),
#                 knowledge_id=knowledge_id,
#                 update_time=update_time.isoformat()
#             ))
#
#         return chunks
#
#
# markdown_parser = MarkdownParser()
