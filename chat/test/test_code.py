function_str = """
def add(a, b):
    return a + b
"""

# 编译字符串为代码对象
compiled_code = compile(function_str, '<string>', 'exec')

# 执行代码对象
exec(compiled_code)

# 调用函数
result = add(3, 5)
print(result)  # 输出: 8


# code_str = '''
#
# class Student:
#     name: str
#     age: int = 0
#     # 个人信息
#     info: str = field(init=False)
#
#     def __post_init__(self):
#         self.info = f'我的名字叫{self.name}, 今年{self.age}岁了'
#
# stu = Student("张三", 20)
# return stu
# '''
#
# # 将代码字符串包装在一个生成器表达式中
# generator_expression = f"({code_str.replace('return', 'yield')} for _ in [None])"
#
# # 使用 exec() 执行生成器表达式
# namespace = {}
# exec(f"generator = {generator_expression}", globals(), namespace)
#
# # 获取生成器的第一个（也是唯一一个）值
# generator = namespace['generator']
# result = next(generator)
#
# # 打印结果
# print(result)