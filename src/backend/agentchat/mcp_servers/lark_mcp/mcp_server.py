from lark_mcp.mcp_tool.user_info.batch_get_id_user import get_user_info_request
from lark_mcp.mcp_tool.user_info.get_user_info import batch_get_user_info
from lark_mcp.mcp_tool.document.create_document import create_document
from lark_mcp.mcp_tool.document.get_document_data import get_document
from lark_mcp.mcp_tool.folder.create_folder import create_folder
from lark_mcp.mcp_tool.folder.list_folder_files import list_folder_files
from lark_mcp.mcp_tool.message.create_message import create_message
from lark_mcp.mcp_tool.calendar.create_calendar import create_calendar
from lark_mcp.mcp_tool.calendar.delete_calendar import delete_calendar
from lark_mcp.mcp_tool.calendar.get_calendar_info import get_calendar_info
from lark_mcp.mcp_tool.calendar.get_calendar_list import get_calendars_list
from lark_mcp.mcp_tool.calendar.update_calendar import update_calendar
from lark_mcp.mcp_tool.calendar_event.create_calendar_event import create_calendar_event
from lark_mcp.mcp_tool.calendar_event.append_calendar_event_attendees import append_calendar_event_attendee
from lark_mcp.mcp_tool.calendar_event.get_calendar_event_info import get_calendar_event
from lark_mcp.mcp_tool.calendar_event.update_calendar_event import update_calendar_event
from lark_mcp.mcp_tool.calendar_event.delete_calendar_event import delete_calendar_event
from mcp.server.fastmcp import FastMCP


def register_mcp_server(mcp: FastMCP):
    # 用户管理
    # mcp.tool(description=get_id_user_request.__doc__)(get_id_user_request)
    mcp.tool(description=batch_get_user_info.__doc__)(batch_get_user_info)

    # 日程管理
    mcp.tool(description=create_calendar_event.__doc__)(create_calendar_event)
    mcp.tool(description=append_calendar_event_attendee.__doc__)(append_calendar_event_attendee)
    mcp.tool(description=get_calendar_event.__doc__)(get_calendar_event)
    mcp.tool(description=update_calendar_event.__doc__)(update_calendar_event)
    mcp.tool(description=delete_calendar_event.__doc__)(delete_calendar_event)

    # 日历管理
    mcp.tool(description=create_calendar.__doc__)(create_calendar)
    mcp.tool(description=delete_calendar.__doc__)(delete_calendar)
    mcp.tool(description=get_calendar_info.__doc__)(get_calendar_info)
    mcp.tool(description=get_calendars_list.__doc__)(get_calendars_list)
    mcp.tool(description=update_calendar.__doc__)(update_calendar)

    # 文档管理
    mcp.tool(description=create_document.__doc__)(create_document)
    mcp.tool(description=get_document.__doc__)(get_document)

    # 文件夹管理
    mcp.tool(description=create_folder.__doc__)(create_folder)
    mcp.tool(description=list_folder_files.__doc__)(list_folder_files)

    # 消息管理
    mcp.tool(description=create_message.__doc__)(create_message)

    # 群聊管理 (Lark-MCP V1.0不上线)
    # mcp.tool(description=create_chat_member.__doc__)(create_chat_member)
    # mcp.tool(description=delete_chat_member.__doc__)(delete_chat_member)
    # mcp.tool(description=get_chat_member_info.__doc__)(get_chat_member_info)