from agentchat.settings import app_settings


class ESIndex:
    """根据配置自动切换是否使用 IK 分词器"""

    use_ik = app_settings.rag.enable_ik_analyzer

    # delete
    index_delete = """
    {
        "query": {
            "term": {
                "file_id": "%s"
            }
        }
    }
    """

    # search content
    _index_search_content_template = """
    {
      "size": 10,
      "timeout": "3s",
      "query": {
        "match": {
          "content": {
            "query": "%s",
            __ANALYZER__
            "operator": "and",
            "minimum_should_match": "75%%",
            "fuzziness": "AUTO",
            "boost": 2.0
          }
        }
      }
    }
    """

    # search summary
    _index_search_summary_template = """
    {
      "size": 10,
      "timeout": "3s",
      "query": {
        "match": {
          "summary": {
            "query": "%s",
            __ANALYZER__
            "operator": "and",
            "minimum_should_match": "75%%",
            "fuzziness": "AUTO",
            "boost": 2.0
          }
        }
      }
    }
    """

    # config
    if use_ik:
        _analyzer_str = '"analyzer": "ik_smart",'

        index_config = """
        {
          "settings": {
            "analysis": {
              "analyzer": {
                "ik_analyzer": {
                  "type": "custom",
                  "tokenizer": "ik_smart"
                }
              }
            }
          },
          "mappings": {
            "properties": {
              "chunk_id": {"type": "keyword"},
              "content": {"type": "text", "analyzer": "ik_analyzer"},
              "summary": {"type": "text", "analyzer": "ik_analyzer"},
              "file_id": {"type": "keyword"},
              "knowledge_id": {"type": "keyword"},
              "file_name": {"type": "keyword"},
              "update_time": {
                "type": "date",
                "format": "strict_date_optional_time||epoch_millis"
              }
            }
          }
        }
        """
    else:
        _analyzer_str = ""

        index_config = """
        {
          "mappings": {
            "properties": {
              "chunk_id": {"type": "keyword"},
              "content": {"type": "text"},
              "summary": {"type": "text"},
              "file_id": {"type": "keyword"},
              "knowledge_id": {"type": "keyword"},
              "file_name": {"type": "keyword"},
              "update_time": {
                "type": "date",
                "format": "strict_date_optional_time||epoch_millis"
              }
            }
          }
        }
        """

    # 最终生成（只替换 analyzer，不动 JSON 结构）
    index_search_content = _index_search_content_template.replace(
        "__ANALYZER__", _analyzer_str
    )

    index_search_summary = _index_search_summary_template.replace(
        "__ANALYZER__", _analyzer_str
    )