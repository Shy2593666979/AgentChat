from datetime import datetime
from typing import Union, Dict, Any, ClassVar, Set

from sqlmodel.main import IncEx
from typing_extensions import Literal

import orjson
from sqlmodel import SQLModel
from pydantic import ConfigDict


def orjson_dumps(v, *, default=None, sort_keys=False, indent_2=True):
    option = orjson.OPT_SORT_KEYS if sort_keys else None
    if indent_2:
        # orjson.dumps returns bytes, to match standard json.dumps we need to decode
        # option
        # To modify how data is serialized, specify option. Each option is an integer constant in orjson.
        # To specify multiple options, mask them together, e.g., option=orjson.OPT_STRICT_INTEGER | orjson.OPT_NAIVE_UTC
        if option is None:
            option = orjson.OPT_INDENT_2
        else:
            option |= orjson.OPT_INDENT_2
    if default is None:
        return orjson.dumps(v, option=option).decode()
    return orjson.dumps(v, default=default, option=option).decode()


class SQLModelSerializable(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    # 使用ClassVar标注类变量，不会被视为模型字段
    hide_fields: ClassVar[list[str]] = [] # "api_key"

    def to_dict(self):
        result = self.model_dump(exclude=self.hide_fields)
        for column in result:
            value = getattr(self, column)
            if isinstance(value, datetime):
                # 将datetime对象转换为字符串
                value = value.isoformat()
            result[column] = value
        return result
