REDIS_URL = "redis://localhost:6379"

MYSQL_URL = "mysql+pymysql://root:mingguang0703@localhost:3306/agentchat"

SERVICE_HOST = "127.0.0.1"

SERVICE_PORT = 8880

TOOL_OPENAI = "tools/function_openai.json"

AGENT_DEFAULT_LOGO = "img/agent/assistant.png"

TOOL_DEFAULT_LOGO = "img/tool/tool.png"

LOGO_PREFIX = "http://" + SERVICE_HOST + ":" + str(SERVICE_PORT) + "/"

SUCCESS_RESP = True

FAIL_RESP = False

OSS_ACCESS_KEY_ID = ""

OSS_ACCESS_KEY_SECRET = ""

OSS_ENDPOINT = "oss-cn-beijing.aliyuncs.com"

OSS_BUCKET_NAME = "agentchat"

OSS_BASE_URL = f"https://{OSS_BUCKET_NAME}.{OSS_ENDPOINT}"
