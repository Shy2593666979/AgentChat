# -------------------------------
# 该文件目前版本已弃用
# -------------------------------
from data import get_function_by_name_type

class BotCheck:
    
    @classmethod
    def slot_is_full(cls, function_args, function_name):
        for key, value in function_args.items():
            # 检查字段是否为空
            if value== "":
                return False
        if len(cls.no_mention_parameters(function_args, function_name)) != 0:
            return False

        return True
    
    @classmethod
    def lack_parameters(cls, function_args, function_name):
        slot = []
        for key, value in function_args.items():
            if value == "":
                slot.append(key)
        
        return slot + cls.no_mention_parameters(function_args, function_name)

    @classmethod
    def no_mention_parameters(cls, function_args, function_name):
        required_fields = cls._get_need_parameter(function_name)
        slot = []
        for key in required_fields:
            if not function_args.get(key):
                slot.append(key)
        return slot

    @classmethod
    def have_parameters(cls, function_args):
        slot = []
        for key, value in function_args.items():
            if key != "":
                slot.append({key: value})
        return slot

    @classmethod
    def _get_need_parameter(cls, function_name):
        function = get_function_by_name_type(function_name=function_name)
        required_fields = function['parameters']['required']
        return required_fields
