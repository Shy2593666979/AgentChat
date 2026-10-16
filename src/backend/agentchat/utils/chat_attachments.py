from urllib.parse import unquote, urlparse


def attachment_events(req):
    """附件元数据随用户消息保存到现有 events 字段，无需变更数据库表。"""
    if not req.file_url:
        return []
    name = req.file_name or unquote(urlparse(req.file_url).path.rsplit("/", 1)[-1]) or "附件"
    data = {
        "url": req.file_url,
        "name": name,
    }
    if req.file_size is not None:
        data["size"] = req.file_size
    if req.file_type:
        data["mime"] = req.file_type
    return [
        {
            "type": "attachment",
            "data": data,
        }
    ]
