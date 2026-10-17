
import json
from typing import Dict, List, Optional

from loguru import logger
from tavily import TavilyClient

from agentchat.core.models.manager import ModelManager
from agentchat.settings import app_settings


# 一个简单的测试，没有入选Mars Tools列表内
class SimpleLLMJudge:
    """简单的LLM判断器"""

    def __init__(self):
        self.LLM = ModelManager.get_chat_model()

    def judge_and_decide(self, original_query: str, search_results: str) -> Dict:
        """判断搜索结果并决定下一步"""

        # 简化的prompt
        prompt = f"""
        用户问题：{original_query}
        
        当前搜索结果：
        {search_results}
        
        请判断这些结果是否足够回答用户问题。如果不够，建议一个新的搜索词。
        
        请用JSON格式回复：
        {{
            "sufficient": true/false,
            "score": 1-10,
            "next_query": "如果不够的话，建议的新搜索词，如果够了就填null",
            "reason": "简短说明"
        }}
        """

        try:
            response = self.LLM.invoke(prompt)
            content = response.content

            # 尝试解析JSON
            try:
                return json.loads(content)
            except:
                # 解析失败时的默认返回
                return {
                    "sufficient": True,
                    "score": 5,
                    "next_query": None,
                    "reason": "解析失败，停止搜索"
                }

        except Exception as e:
            logger.error(f"LLM判断失败: {e}")
            return {
                "sufficient": True,
                "score": 5,
                "next_query": None,
                "reason": f"请求失败: {e}"
            }


class SimpleIterativeSearch:
    """简单的迭代搜索系统"""

    def __init__(self, tavily_api_key: str):
        self.tavily_client = TavilyClient(tavily_api_key)
        self.llm_judge = SimpleLLMJudge()
        self.max_iterations = 3

    def search_with_judgment(self, query: str, max_results: int = 10) -> str:
        """执行带判断的迭代搜索"""

        original_query = query
        current_query = query
        all_results = []
        iteration = 0

        logger.debug(f"🔍 开始搜索: {query}")

        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"\n--- 第 {iteration} 次搜索 ---")
            logger.debug(f"搜索词: {current_query}")

            # 使用Tavily搜索
            try:
                response = self.tavily_client.search(
                    query=current_query,
                    max_results=max_results,
                    time_range="month", # 时间跨度为近一月内的事情
                    include_raw_content="markdown",
                    country="china"
                )

                # 格式化当前搜索结果
                current_formatted = self._format_tavily_results(response)
                all_results.append({
                    "iteration": iteration,
                    "query": current_query,
                    "results": current_formatted,
                    "raw_response": response
                })

                logger.info(f"✅ 找到 {len(response.get('results', []))} 个结果")

                # 让LLM判断结果质量
                judgment = self.llm_judge.judge_and_decide(original_query, current_formatted)

                logger.info(f"📊 质量评分: {judgment['score']}/10")
                logger.debug(f"💭 判断: {judgment['reason']}")

                # 如果结果足够，停止搜索
                if judgment["sufficient"] or not judgment["next_query"]:
                    logger.info("✅ 搜索完成")
                    break

                # 准备下一次搜索
                if iteration < self.max_iterations:
                    current_query = judgment["next_query"]
                    logger.debug(f"🔄 继续搜索: {current_query}")

            except Exception as e:
                logger.error(f"❌ 搜索失败: {e}")
                break

        # 整合所有结果
        final_result = self._combine_results(all_results)
        logger.info(f"\n🎯 完成！共搜索 {iteration} 次")

        return final_result

    def _format_tavily_results(self, response: Dict) -> str:
        """格式化Tavily搜索结果"""
        if not response.get("results"):
            return "未找到相关结果"

        formatted = []
        for result in response["results"]:
            url = result.get("url", "")
            title = result.get("title", "")
            content = result.get("content", "")
            formatted.append(f"标题: {title}\n网址: {url}\n内容: {content}")

        return "\n\n".join(formatted)

    def _combine_results(self, all_results: List[Dict]) -> str:
        """整合所有搜索结果"""
        if not all_results:
            return "未获得任何搜索结果"

        combined = []
        for result_set in all_results:
            combined.append(f"=== 第{result_set['iteration']}次搜索: {result_set['query']} ===")
            combined.append(result_set['results'])
            combined.append("")

        return "\n".join(combined)


# 使用示例
def main():
    # 配置API密钥
    tavily_api_key = "tvly-dev-********************************"  # 你的Tavily API密钥
    llm_api_key = "sk-********************************"  # 你的LLM API密钥

    # 如果使用其他LLM服务，修改base_url
    # llm_base_url = "https://api.deepseek.com/v1"  # 例如DeepSeek
    # llm_base_url = "https://api.openai.com/v1"    # OpenAI

    # 创建搜索系统
    search_system = SimpleIterativeSearch(
        tavily_api_key=tavily_api_key,
        # llm_api_key=llm_api_key,
        # llm_base_url=llm_base_url  # 如果需要指定其他服务
    )

    # 执行搜索
    query = "AI的新闻"
    results = search_system.search_with_judgment(
        query=query,
        max_results=5
    )

    logger.info("\n" + "=" * 60)
    logger.info("最终搜索结果:")
    logger.info("=" * 60)
    logger.debug(results)
