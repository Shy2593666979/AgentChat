from typing import Any


def resp_200(data: Any=None, code: int=200, message: str="SUCCESS"):
    return {
        "code": code,
        "message": message,
        "data": data
    }

def resp_500(data: Any=None, code: int=500, message: str="REQUEST ERROR"):
    return {
        "code": code,
        "message": message,
        "data": data
    }