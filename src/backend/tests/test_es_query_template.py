"""ES 关键词检索模板：必须能“部分词命中”召回，否则混合检索退化为纯向量检索。

历史问题：operator=and + minimum_should_match=75%，IK 分词后任何一句问话都要求
全部词都出现，导致 ES 永远 0 命中。
"""
import json

from agentchat.config.es_index import ESIndex


def build_body(template, query="报销流程是什么"):
    return json.loads(template % query)


def test_content_query_uses_or_with_partial_match():
    clause = build_body(ESIndex.index_search_content)["query"]["match"]["content"]
    assert clause["operator"] == "or"
    assert clause["minimum_should_match"] == "60%"
    assert "fuzziness" not in clause
    assert clause["query"] == "报销流程是什么"


def test_summary_query_uses_or_with_partial_match():
    clause = build_body(ESIndex.index_search_summary)["query"]["match"]["summary"]
    assert clause["operator"] == "or"
    assert clause["minimum_should_match"] == "60%"


def test_analyzer_follows_ik_setting():
    clause = build_body(ESIndex.index_search_content)["query"]["match"]["content"]
    if ESIndex.use_ik:
        assert clause["analyzer"] == "ik_smart"
    else:
        assert "analyzer" not in clause


def test_template_is_valid_json_for_plain_query():
    body = build_body(ESIndex.index_search_content, "年假多少天")
    assert body["size"] == 10
    assert body["timeout"] == "3s"
