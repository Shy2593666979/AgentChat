class ESIndex:
    index_delete = """{{
        "query": {{
            "term": {{
                "file_id": "{file_id}"
            }}
        }}
    }}"""

    index_search_content = """{{
      "size": 10,
      "timeout": "3s",
      "query": {{
        "match": {{
          "content": {{
            "query": "{query}",
            "analyzer": "ik_smart",
            "operator": "and",
            "minimum_should_match": "75%",
            "fuzziness": "AUTO",
            "boost": 2.0
          }}
        }}
      }}
    }}"""

    index_search_summary = """{{
          "size": 10,
          "timeout": "3s",
          "query": {{
            "match": {{
              "content": {{
                "query": "{query}",
                "analyzer": "ik_smart",
                "operator": "and",
                "minimum_should_match": "75%",
                "fuzziness": "AUTO",
                "boost": 2.0
              }}
            }}
          }}
        }}"""

    index_config = """{
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
          "chunk_id": {
            "type": "keyword"
          },
          "content": {
            "type": "text",
            "analyzer": "ik_analyzer"
          },
          "summary": {
            "type": "text",
            "analyzer": "ik_analyzer"
          },
          "file_id": {
            "type": "keyword"
          },
          "knowledge_id": {
            "type": "keyword"
          },
          "file_name": {
            "type": "keyword"
          },
          "update_time": {
            "type": "date",
            "format": "strict_date_optional_time||epoch_millis"
          }
        }
      }
    }"""
