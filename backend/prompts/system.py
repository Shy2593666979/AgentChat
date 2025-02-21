system_query_rewrite = """
{
  "instruction": "请将用户输入的query用三种不同的表达方式改写，保持原意但改变句式结构和用词",
  "output_rules": {
    "format": "JSON",
    "structure": {
      "original_query": "string",
      "variations": ["string", "string", "string"]
    },
    "requirements": [
      "三种问法应使用不同的句式结构",
      "需保持核心语义不变",
      "避免使用专业术语简化表达"
    ]
  },
  "example": {
    "input": {
      "query": "如何提高睡眠质量"
    },
    "output": [
        "有什么方法可以改善夜间休息效果？",
        "怎样做才能获得更好的睡眠？",
        "提升睡眠品质的有效措施有哪些？"
      ]
  }
}
"""