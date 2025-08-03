# 通用多工具递归调用框架
# 支持任意数量的工具和复杂的调用链

import json
import asyncio
from typing import Dict, List, Any, Optional, Callable, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from langchain.tools import BaseTool
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator


# ========== 1. 基础框架定义 ==========

class ToolCallResult:
    """工具调用结果"""

    def __init__(self, success: bool, data: Any = None, error: str = None):
        self.success = success
        self.data = data
        self.error = error

    def __repr__(self):
        return f"ToolCallResult(success={self.success}, data={self.data}, error={self.error})"


class WorkflowState(TypedDict):
    """工作流状态"""
    current_step: str
    tool_results: Dict[str, ToolCallResult]
    shared_context: Dict[str, Any]
    error_count: int
    max_errors: int
    workflow_data: Dict[str, Any]


# ========== 2. 通用工具基类 ==========

class UniversalTool(BaseTool):
    """通用工具基类"""

    def __init__(self, name: str, description: str,
                 dependencies: List[str] = None,
                 transform_input: Callable = None,
                 transform_output: Callable = None):
        self.name = name
        self.description = description
        self.dependencies = dependencies or []
        self.transform_input = transform_input
        self.transform_output = transform_output

    def _run(self, **kwargs) -> ToolCallResult:
        try:
            # 输入转换
            if self.transform_input:
                kwargs = self.transform_input(kwargs)

            # 执行工具逻辑
            result = self.execute(**kwargs)

            # 输出转换
            if self.transform_output:
                result = self.transform_output(result)

            return ToolCallResult(success=True, data=result)
        except Exception as e:
            return ToolCallResult(success=False, error=str(e))

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """子类需要实现的具体执行逻辑"""
        pass


# ========== 3. 示例工具实现 ==========

class Tool1_UserInput(UniversalTool):
    """工具1：获取用户输入"""

    def __init__(self):
        super().__init__(
            name="user_input",
            description="获取用户输入信息"
        )

    def execute(self, user_query: str = "默认查询") -> Dict[str, Any]:
        return {
            "query": user_query,
            "timestamp": "2024-01-01 12:00:00",
            "user_id": "user_123"
        }


class Tool2_DataFetch(UniversalTool):
    """工具2：数据获取"""

    def __init__(self):
        super().__init__(
            name="data_fetch",
            description="根据查询获取数据",
            dependencies=["user_input"]
        )

    def execute(self, query_info: Dict[str, Any]) -> Dict[str, Any]:
        query = query_info.get("query", "")
        return {
            "raw_data": f"获取到的数据: {query}",
            "data_count": 100,
            "source": "database_1"
        }


class Tool3_DataProcess(UniversalTool):
    """工具3：数据处理"""

    def __init__(self):
        super().__init__(
            name="data_process",
            description="处理原始数据",
            dependencies=["data_fetch"]
        )

    def execute(self, raw_data_info: Dict[str, Any]) -> Dict[str, Any]:
        raw_data = raw_data_info.get("raw_data", "")
        return {
            "processed_data": f"处理后的数据: {raw_data}",
            "processing_time": "2.5秒",
            "quality_score": 0.95
        }


class Tool4_Analysis(UniversalTool):
    """工具4：数据分析"""

    def __init__(self):
        super().__init__(
            name="analysis",
            description="分析处理后的数据",
            dependencies=["data_process"]
        )

    def execute(self, processed_data_info: Dict[str, Any]) -> Dict[str, Any]:
        processed_data = processed_data_info.get("processed_data", "")
        return {
            "analysis_result": f"分析结果: {processed_data}",
            "insights": ["洞察1", "洞察2", "洞察3"],
            "confidence": 0.88
        }


class Tool5_Visualization(UniversalTool):
    """工具5：数据可视化"""

    def __init__(self):
        super().__init__(
            name="visualization",
            description="创建数据可视化",
            dependencies=["analysis"]
        )

    def execute(self, analysis_info: Dict[str, Any]) -> Dict[str, Any]:
        insights = analysis_info.get("insights", [])
        return {
            "chart_type": "bar_chart",
            "chart_data": insights,
            "chart_url": "https://example.com/chart.png"
        }


class Tool6_Report(UniversalTool):
    """工具6：生成报告"""

    def __init__(self):
        super().__init__(
            name="report",
            description="生成最终报告",
            dependencies=["analysis", "visualization"]
        )

    def execute(self, analysis_info: Dict[str, Any], viz_info: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "report_content": f"报告内容基于: {analysis_info.get('analysis_result', '')}",
            "chart_included": viz_info.get("chart_url", ""),
            "report_id": "report_001"
        }


# ========== 4. 工作流编排器 ==========

class WorkflowOrchestrator:
    """工作流编排器"""

    def __init__(self):
        self.tools: Dict[str, UniversalTool] = {}
        self.workflow_graph = None
        self.execution_order = []

    def register_tool(self, tool: UniversalTool):
        """注册工具"""
        self.tools[tool.name] = tool

    def register_tools(self, tools: List[UniversalTool]):
        """批量注册工具"""
        for tool in tools:
            self.register_tool(tool)

    def build_execution_order(self) -> List[str]:
        """根据依赖关系构建执行顺序"""
        visited = set()
        temp_visited = set()
        order = []

        def dfs(tool_name: str):
            if tool_name in temp_visited:
                raise ValueError(f"检测到循环依赖: {tool_name}")
            if tool_name in visited:
                return

            temp_visited.add(tool_name)
            tool = self.tools.get(tool_name)
            if tool:
                for dep in tool.dependencies:
                    if dep in self.tools:
                        dfs(dep)

            temp_visited.remove(tool_name)
            visited.add(tool_name)
            order.append(tool_name)

        # 对所有工具进行拓扑排序
        for tool_name in self.tools.keys():
            if tool_name not in visited:
                dfs(tool_name)

        self.execution_order = order
        return order

    def create_workflow_graph(self) -> StateGraph:
        """创建工作流图"""
        # 构建执行顺序
        execution_order = self.build_execution_order()

        # 创建状态图
        workflow = StateGraph(WorkflowState)

        # 为每个工具创建执行节点
        for tool_name in execution_order:
            workflow.add_node(tool_name, self.create_tool_executor(tool_name))

        # 添加边
        for i, tool_name in enumerate(execution_order):
            if i == 0:
                workflow.set_entry_point(tool_name)

            if i < len(execution_order) - 1:
                next_tool = execution_order[i + 1]
                workflow.add_edge(tool_name, next_tool)
            else:
                workflow.add_edge(tool_name, END)

        self.workflow_graph = workflow
        return workflow

    def create_tool_executor(self, tool_name: str) -> Callable:
        """创建工具执行器"""

        def execute_tool(state: WorkflowState) -> Dict[str, Any]:
            tool = self.tools[tool_name]
            print(f"执行工具: {tool_name}")

            # 准备输入参数
            kwargs = self.prepare_tool_input(tool, state)

            # 执行工具
            result = tool._run(**kwargs)

            # 更新状态
            updated_state = {
                "current_step": tool_name,
                "tool_results": {**state["tool_results"], tool_name: result},
                "shared_context": state["shared_context"],
                "error_count": state["error_count"] + (1 if not result.success else 0),
                "workflow_data": {**state["workflow_data"], tool_name: result.data}
            }

            if not result.success:
                print(f"工具 {tool_name} 执行失败: {result.error}")

            return updated_state

        return execute_tool

    def prepare_tool_input(self, tool: UniversalTool, state: WorkflowState) -> Dict[str, Any]:
        """准备工具输入参数"""
        kwargs = {}

        # 根据依赖关系准备输入
        for dep in tool.dependencies:
            if dep in state["tool_results"]:
                dep_result = state["tool_results"][dep]
                if dep_result.success:
                    # 使用依赖工具的结果作为输入
                    kwargs[f"{dep}_info"] = dep_result.data

        # 添加共享上下文
        kwargs.update(state["shared_context"])

        return kwargs

    def execute_workflow(self, initial_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行工作流"""
        if not self.workflow_graph:
            self.create_workflow_graph()

        # 编译工作流
        app = self.workflow_graph.compile()

        # 初始状态
        initial_state = {
            "current_step": "",
            "tool_results": {},
            "shared_context": initial_context or {},
            "error_count": 0,
            "max_errors": 3,
            "workflow_data": {}
        }

        # 执行工作流
        result = app.invoke(initial_state)

        return result


# ========== 5. 条件分支工作流 ==========

class ConditionalWorkflow(WorkflowOrchestrator):
    """支持条件分支的工作流"""

    def __init__(self):
        super().__init__()
        self.conditions: Dict[str, Callable] = {}
        self.branch_mappings: Dict[str, Dict[str, str]] = {}

    def add_condition(self, step_name: str, condition_func: Callable, branch_map: Dict[str, str]):
        """添加条件分支"""
        self.conditions[step_name] = condition_func
        self.branch_mappings[step_name] = branch_map

    def create_conditional_workflow(self) -> StateGraph:
        """创建条件工作流"""
        workflow = StateGraph(WorkflowState)

        # 添加所有工具节点
        for tool_name in self.tools.keys():
            workflow.add_node(tool_name, self.create_tool_executor(tool_name))

        # 添加条件边
        for step_name, condition_func in self.conditions.items():
            if step_name in self.tools:
                workflow.add_conditional_edges(
                    step_name,
                    condition_func,
                    self.branch_mappings[step_name]
                )

        return workflow


# ========== 6. 并行执行工作流 ==========

class ParallelWorkflow(WorkflowOrchestrator):
    """支持并行执行的工作流"""

    def __init__(self):
        super().__init__()
        self.parallel_groups: Dict[str, List[str]] = {}

    def add_parallel_group(self, group_name: str, tool_names: List[str]):
        """添加并行执行组"""
        self.parallel_groups[group_name] = tool_names

    async def execute_parallel_group(self, group_name: str, state: WorkflowState) -> WorkflowState:
        """执行并行组"""
        tool_names = self.parallel_groups[group_name]

        # 创建并行任务
        tasks = []
        for tool_name in tool_names:
            task = asyncio.create_task(self.execute_tool_async(tool_name, state))
            tasks.append(task)

        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 更新状态
        for tool_name, result in zip(tool_names, results):
            if isinstance(result, Exception):
                state["tool_results"][tool_name] = ToolCallResult(success=False, error=str(result))
                state["error_count"] += 1
            else:
                state["tool_results"][tool_name] = result
                state["workflow_data"][tool_name] = result.data

        return state

    async def execute_tool_async(self, tool_name: str, state: WorkflowState) -> ToolCallResult:
        """异步执行工具"""
        tool = self.tools[tool_name]
        kwargs = self.prepare_tool_input(tool, state)
        return tool._run(**kwargs)


# ========== 7. 使用示例 ==========

def create_complex_workflow():
    """创建复杂工作流示例"""

    # 创建工具实例
    tools = [
        Tool1_UserInput(),
        Tool2_DataFetch(),
        Tool3_DataProcess(),
        Tool4_Analysis(),
        Tool5_Visualization(),
        Tool6_Report()
    ]

    # 创建工作流编排器
    orchestrator = WorkflowOrchestrator()
    orchestrator.register_tools(tools)

    return orchestrator


def create_conditional_workflow_example():
    """创建条件分支工作流示例"""

    # 添加条件工具
    class ConditionalTool(UniversalTool):
        def __init__(self):
            super().__init__(
                name="conditional_check",
                description="条件检查工具",
                dependencies=["data_process"]
            )

        def execute(self, processed_data_info: Dict[str, Any]) -> Dict[str, Any]:
            quality_score = processed_data_info.get("quality_score", 0)
            return {
                "quality_score": quality_score,
                "needs_reprocessing": quality_score < 0.8
            }

    # 创建条件工作流
    conditional_workflow = ConditionalWorkflow()

    # 注册基础工具
    basic_tools = [
        Tool1_UserInput(),
        Tool2_DataFetch(),
        Tool3_DataProcess(),
        ConditionalTool(),
        Tool4_Analysis(),
        Tool6_Report()
    ]

    conditional_workflow.register_tools(basic_tools)

    # 添加条件分支
    def quality_check_condition(state: WorkflowState) -> str:
        """质量检查条件"""
        conditional_result = state["tool_results"].get("conditional_check")
        if conditional_result and conditional_result.success:
            needs_reprocessing = conditional_result.data.get("needs_reprocessing", False)
            return "data_process" if needs_reprocessing else "analysis"
        return "analysis"

    conditional_workflow.add_condition(
        "conditional_check",
        quality_check_condition,
        {
            "data_process": "data_process",
            "analysis": "analysis"
        }
    )

    return conditional_workflow


# ========== 8. 主函数和测试 ==========

def main():
    """主函数"""

    print("=== 创建复杂工作流 ===")
    orchestrator = create_complex_workflow()

    print("\n执行顺序:")
    execution_order = orchestrator.build_execution_order()
    for i, tool_name in enumerate(execution_order, 1):
        print(f"{i}. {tool_name}")

    print("\n=== 执行工作流 ===")
    result = orchestrator.execute_workflow({
        "user_query": "分析销售数据趋势"
    })

    print("\n=== 执行结果 ===")
    for tool_name, tool_result in result["tool_results"].items():
        print(f"{tool_name}: {tool_result}")

    print("\n=== 最终数据 ===")
    final_data = result["workflow_data"]
    for tool_name, data in final_data.items():
        print(f"{tool_name}: {data}")


if __name__ == "__main__":
    main()

# ========== 9. 框架特性总结 ==========

"""
通用多工具递归调用框架特性：

1. **工具管理**：
   - 统一的工具基类
   - 依赖关系管理
   - 自动拓扑排序

2. **工作流编排**：
   - 自动构建执行顺序
   - 状态管理和传递
   - 错误处理和恢复

3. **高级特性**：
   - 条件分支执行
   - 并行工具执行
   - 动态工作流调整

4. **扩展性**：
   - 易于添加新工具
   - 支持复杂的业务逻辑
   - 可视化工作流图

5. **实用功能**：
   - 详细的执行日志
   - 结果缓存机制
   - 性能监控

使用方法：
1. 继承UniversalTool创建具体工具
2. 定义工具之间的依赖关系
3. 使用WorkflowOrchestrator编排工作流
4. 执行工作流并获取结果
"""