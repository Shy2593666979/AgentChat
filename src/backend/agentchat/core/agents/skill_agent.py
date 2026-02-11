from loguru import logger
from typing import Optional, Union, Dict, Literal, List
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.config import get_stream_writer
from langgraph.prebuilt.tool_node import ToolCallRequest

from agentchat.core.callbacks import usage_metadata_callback
from agentchat.core.models.manager import ModelManager
from agentchat.database import AgentSkill
from agentchat.schema.agent_skill import AgentSkillFolder, AgentSkillFile


class SkillAgent:

    def __init__(
        self,
        skill: AgentSkill,
        user_id: str
    ):
        self.skill = skill
        self.user_id = user_id
        self.skill_folder: Optional[AgentSkillFolder] = None
        self.file_cache: Dict[str, AgentSkillFile] = {}  # 路径 -> 文件对象

        self.conversation_model = None
        self.tool_invocation_model = None
        self.tools = None
        self.middlewares = None
        self.react_agent = None

        self._initialized = False

    async def init_skill_agent(self):
        """初始化技能Agent的所有组件"""
        try:
            self.load_skill_folder(self.skill.folder)

            self.setup_language_model()
            self.tools = self.setup_skill_agent_tools()
            self.middlewares = await self.setup_agent_middlewares()
            self.react_agent = self.setup_react_agent()

            self._initialized = True
            logger.info(f"SkillAgent '{self.skill.name}' 初始化成功")
        except Exception as e:
            logger.error(f"SkillAgent 初始化失败: {e}")
            raise

    def setup_react_agent(self):
        """设置 ReAct Agent"""
        if not self.conversation_model:
            raise ValueError("语言模型未初始化")

        skill_md = self.get_skill_md()
        if not skill_md:
            logger.warning(f"技能 '{self.skill.name}' 缺少 SKILL.md 文档")
            skill_md = f"技能名称: {self.skill.name}\n描述: {self.skill.description or '无描述'}"

        return create_agent(
            model=self.conversation_model,
            tools=self.tools,
            middleware=self.middlewares,
            system_prompt=self._build_system_prompt(skill_md)
        )

    def setup_language_model(self):
        """设置语言模型"""
        self.conversation_model = ModelManager.get_conversation_model()
        self.tool_invocation_model = ModelManager.get_tool_invocation_model()


    async def emit_event(self, event):
        writer = get_stream_writer()
        writer(event)

    def _build_system_prompt(self, skill_md: str) -> str:
        """构建系统提示词"""
        return f"""你是一个专门的技能Agent，负责执行 '{self.skill.name}' 技能。

        # 技能文档
        {skill_md}
        
        # 可用工具
        你可以使用 get_file_content 工具来读取技能文件夹中的任何文件。
        
        # 执行原则
        1. 严格遵循技能文档中的指引
        2. 需要额外信息时主动读取相关文件
        3. 给出清晰、结构化的回复
        4. 遇到错误时提供详细的错误信息
        """

    def load_skill_folder(self, json_data: dict) -> AgentSkillFolder:
        """
        递归加载技能文件夹结构

        Args:
            json_data: 技能文件夹的 JSON 数据

        Returns:
            AgentSkillFolder 对象
        """

        # 递归解析函数
        def parse_item(item_data: dict) -> Union[AgentSkillFile, AgentSkillFolder]:
            item_type = item_data.get('type', 'file')

            if item_type == 'file':
                # 创建文件对象
                file_obj = AgentSkillFile(
                    name=item_data['name'],
                    path=item_data['path'],
                    type=item_data['type'],
                    content=item_data.get('content', '')
                )
                # 缓存文件对象，方便快速查找
                self.file_cache[file_obj.path] = file_obj
                return file_obj

            elif item_type == 'folder':
                # 递归处理子文件夹
                folder_items = []
                for sub_item in item_data.get('folder', []):
                    folder_items.append(parse_item(sub_item))

                # 创建文件夹对象
                folder_obj = AgentSkillFolder(
                    name=item_data['name'],
                    path=item_data['path'],
                    type=item_data['type'],
                    folder=folder_items
                )
                return folder_obj

            else:
                raise ValueError(f"Unknown type: {item_type}")

        # 解析根文件夹
        self.skill_folder = parse_item(json_data)
        return self.skill_folder

    def get_file_content(self, path: str) -> Optional[str]:
        """根据路径快速获取文件内容"""
        file_obj = self.file_cache.get(path)
        return file_obj.content if file_obj else None

    def list_files(self, pattern: str = None) -> List[str]:
        """
        列出所有文件路径

        Args:
            pattern: 可选的路径匹配模式（支持简单的字符串包含匹配）

        Returns:
            文件路径列表
        """
        if pattern:
            return [
                path for path in self.file_cache.keys()
                if pattern in path
            ]
        return list(self.file_cache.keys())

    def get_skill_md(self) -> Optional[str]:
        """获取 SKILL.md 文件内容"""
        if not self.skill_folder:
            return None

        # 在根目录查找 SKILL.md
        for item in self.skill_folder.folder:
            if isinstance(item, AgentSkillFile) and item.name == "SKILL.md":
                return item.content

        return None


    async def setup_agent_middlewares(self):

        @wrap_tool_call
        async def add_tool_call_args(
            request: ToolCallRequest,
            handler
        ):
            await self.emit_event(
                {
                    "status": "START",
                    "title": f"Skill-Agent - {self.skill.name}执行可用工具: {request.tool_call["name"]}",
                    "messages": f"正在调用工具 {request.tool_call["name"]}..."
                }
            )

            tool_result = await handler(request)

            await self.emit_event(
                {
                    "status": "END",
                    "title": f"Skill-Agent - {self.skill.name}执行可用工具: {request.tool_call["name"]}",
                    "messages": f"{tool_result}"
                }
            )
            return tool_result

        return [add_tool_call_args]

    def setup_skill_agent_tools(self):

        @tool(parse_docstring=True)
        def get_file_content(file_path: str) -> str:
            """
            根据文件路径获取文件内容

            Args:
                file_path: 要读取的文件路径

            Returns:
                文件的内容，如果文件不存在返回错误信息
            """
            content = self.get_file_content(file_path)
            if content is None:
                available_files = self.list_files()
                return (
                    f"错误: 文件 '{file_path}' 不存在。\n"
                    f"可用文件列表:\n" + "\n".join(f"  - {f}" for f in available_files)
                )
            return content

        @tool(parse_docstring=True)
        def list_skill_files(pattern: str = None) -> str:
            """
            列出技能文件夹中的所有文件

            Args:
                pattern: 可选的路径匹配模式

            Returns:
                文件路径列表（每行一个）
            """
            files = self.list_files(pattern)
            if not files:
                return "没有找到文件"
            return "\n".join(files)

        return [get_file_content, list_skill_files]


    async def ainvoke(self, messages: List[BaseMessage]) -> List[BaseMessage] | str:
        """非流式版本"""
        if not self._initialized:
            await self.init_skill_agent()

        result = await self.react_agent.ainvoke(
            input={"messages": messages},
            config={"callbacks": [usage_metadata_callback]}
        )
        filtered_messages = [
            msg for msg in result["messages"]
            if not isinstance(msg, (HumanMessage, SystemMessage))
        ]

        return filtered_messages
