# Lark MCP 工具文档

这是飞书/Lark OpenAPI MCP（Model Context Protocol）工具，旨在帮助用户快速连接飞书平台并实现 AI Agent 与飞书的高效协作。该工具将飞书开放平台的 API 接口封装为 MCP 工具，使 AI 助手能够直接调用这些接口，实现文档处理、发送消息、日程安排等多种自动化场景。

## 1. 批量获取用户信息（batch_get_user_info）
### 功能描述
根据用户的邮箱或者手机号查找用户的信息（包含用户ID），这个工具不仅可以获取基本的用户匹配信息，还会进一步根据获取到的用户ID查询更详细的用户信息，提供更全面的用户数据。
### 所需参数
- user_id_type：用户ID类型，默认为open_id。
- emails：列表的形式，最多50个邮箱，不支持企业邮箱，与mobiles独立查询，可选参数。
- mobiles：列表的形式，最多50个手机号，海外需带国家代码+xxx，与emails独立查询，可选参数。
- include_resigned：是否包含已离职员工，true/false，默认值为True。

---

## 2. 创建日程事件（create_calendar_event）
### 功能描述
创建飞书日程事件，日程创建成功返回日程信息，失败返回错误信息。支持设置时间、地点、参与者、重复规则等完整的日程属性，并可以自动邀请参与者。
### 所需参数
- summary：日程标题，必填参数。
- description：日程描述，必填参数。
- calendar_id：日历ID，必填参数。
- start_time：开始时间，格式YYYY-MM-DD HH:MM，必填参数。
- end_time：结束时间，格式YYYY-MM-DD HH:MM，必填参数。
- user_id_type：用户ID类型，默认值为open_id。
- need_notification：更新日程时，是否给日程参与人发送通知，默认为True。
- location_name：日程的会议位置，可选参数。
- location_address：日程的会议具体地点，如301会议室，可选参数。
- attendees：参会者列表，每个元素需包含用户的open_id，可选参数。
- timezone：时区，默认为Asia/Shanghai。
- visibility：日程公开范围，默认为default。
- attendee_ability：参与者权限，默认为can_see_others。
- free_busy_status：日程占用的忙闲状态，新建日程默认为busy。
- recurrence：遵循日历RRule重复规则，如FREQ=DAILY;INTERVAL=1，默认为FREQ=DAILY;INTERVAL=1。

---

## 3. 添加日程参会者（append_calendar_event_attendee）
### 功能描述
为日程事件添加参会者，成功返回日程信息，失败返回报错信息。可以为已存在的日程添加新的参与者，并选择是否发送通知。
### 所需参数
- calendar_id：日历ID，必填参数。
- event_id：日程事件ID，必填参数。
- attendees：参会者列表，每个元素需包含用户的open_id，必填参数。
- user_id_type：用户ID类型，默认为open_id。可选值：open_id、union_id、user_id。
- need_notification：更新日程时，是否给日程参与人发送通知，默认为True。

---

## 4. 获取日程事件详情（get_calendar_event）
### 功能描述
获取日程事件详细信息，成功返回日程时间详细信息，失败返回报错信息。可以查看日程的完整信息，包括时间、地点、参与者、会议设置等。
### 所需参数
- event_id：日程事件ID，必填参数。
- calendar_id：日历ID，可选参数。
- need_meeting_settings：是否需要返回会议设置信息，默认为True。
- need_attendee：是否需要返回参会者信息，默认为True。
- max_attendee_num：最大返回参会者数量，默认为10。
- user_id_type：用户ID类型，默认为open_id。

---

## 5. 更新日程事件（update_calendar_event）
### 功能描述
更新飞书的日程事件信息，日程创建成功返回日程信息，失败返回错误信息。可以修改日程的各种属性，实现日程信息的动态调整。
### 所需参数
- calendar_id：日历ID，必填参数。
- event_id：日程事件ID，必填参数。
- summary：需要更新的日程标题，必填参数。
- start_time：需要更新的开始时间，格式YYYY-MM-DD HH:MM，必填参数。
- end_time：需要更新的结束时间，格式YYYY-MM-DD HH:MM，必填参数。
- user_id_type：用户ID类型，默认为open_id。
- description：需要更新的日程描述，可选参数。
- location_name：需要更新的日程的会议位置，可选参数。
- location_address：需要更新的日程的会议具体地点，如301会议室，可选参数。
- timezone：需要更新的时区，可选参数。
- visibility：需要更新的日程公开范围，可选参数。
- attendee_ability：需要更新的参与者权限，可选参数。
- free_busy_status：需要更新的日程占用的忙闲状态，新建日程默认为busy，可选参数。
- recurrence：需要更新的重复规则，遵循RRule规则，如FREQ=DAILY;INTERVAL=1，可选参数。

---

## 6. 删除日程事件（delete_calendar_event）
### 功能描述
删除指定的日程事件，成功返回删除成功信息，失败返回报错信息。可以选择是否通知参与者日程的删除。
### 所需参数
- calendar_id：日历ID，必填参数。
- event_id：日程事件ID，必填参数。
- need_notification：是否通知参与者，可选参数。可选值：true-通知，false-不通知，默认为true。

---

## 7. 创建日历（create_calendar）
### 功能描述
创建共享日历，成功返回共享日历信息，失败返回报错信息。可以设置日历的权限、颜色、描述等属性，为团队或个人创建专门的日程管理空间。
### 所需参数
- summary：日历摘要，必填参数。
- description：日历描述，可选参数，默认为空字符串。
- permissions：日历权限，默认为私密。仅支持(私密，展示忙闲，公开)。
- color：日历颜色，默认为-1。其他值：通过RGB值的int32表示，客户端会映射到最接近的色板颜色。
- summary_alias：日历备注名，可选参数。

---

## 8. 删除日历（delete_calendar）
### 功能描述
删除指定共享日历。彻底删除指定的日历，此操作不可逆，会同时删除日历中的所有日程事件。
### 所需参数
- calendar_id：日历ID，必填参数，用于指定要删除的日历。

---

## 9. 获取日历信息（get_calendar_info）
### 功能描述
获取指定的日历信息，成功返回日历信息，失败返回报错信息。用于查看日历的详细配置信息，包括权限、描述、颜色等属性。
### 所需参数
- calendar_id：日历ID，必填参数，用于指定要获取的日历。

---

## 10. 获取日历列表（get_calendars_list）
### 功能描述
获取日历列表，成功返回日历列表，失败返回报错信息。支持分页获取，可以浏览用户有权访问的所有日历。
### 所需参数
- 无额外参数需要，系统默认获取所有的日历，具体还是根据模型上下文决定。

---

## 11. 更新日历（update_calendar）
### 功能描述
根据指定的日历ID更新信息。可以修改日历的各种属性，如标题、描述、权限、颜色等，实现日历信息的动态管理。
### 所需参数
- calendar_id：日历ID，必填参数。
- summary：日历摘要，必填参数。
- description：日历描述，可选参数。
- permissions：日历权限，可选参数。仅支持(私密，展示忙闲，公开)。
- color：日历颜色，可选参数。通过RGB值的int32表示，客户端会映射到最接近的色板颜色。
- summary_alias：日历备注名，可选参数。

---

## 12. 创建文档（create_document）
### 功能描述
创建文档，成功返回文档信息，失败返回报错信息。可以在指定文件夹中创建文档，如果不指定文件夹则在根目录中创建。
### 所需参数
- title：文档标题，必填参数。
- folder_token：文件夹token，可选参数。没有传入的话在根目录中创建。

---

## 13. 获取文档内容（get_document）
### 功能描述
获取文档内容，成功返回文档内容，失败返回报错信息。用于读取已存在文档的完整内容信息。
### 所需参数
- document_id：文档ID，必填参数。

---

## 14. 创建文件夹（create_folder）
### 功能描述
创建文件夹，成功返回文件夹信息，失败返回报错信息。可以在指定的父文件夹下创建新文件夹，实现文件目录结构的管理。
### 所需参数
- name：文件夹名称，必填参数。
- folder_token：父文件夹token，可选参数，默认为空字符串，为空时在根目录创建。

---

## 15. 列出文件夹文件（list_folder_files）
### 功能描述
获取文件夹下的文件列表，成功返回文件列表信息，失败返回报错信息。支持分页获取和排序，可以方便地浏览和管理文件夹中的内容。
### 所需参数
- folder_token：文件夹token，可选参数。不填或为空时获取用户云空间根目录清单（不支持分页），默认为空字符串。
- page_size：每页显示的数据项数量，默认为20。若获取根目录清单，将返回全部数据，范围为1-200。
- order_by：文件排序字段，默认为EditedTime。只允许EditedTime、CreatedTime。
- direction：排序方向，默认为DESC。允许ASC、DESC。
- user_id_type：用户ID类型，默认为open_id。允许open_id、union_id、user_id。

---

## 16. 发送消息（create_message）
### 功能描述
发送消息，给用户发消息需确保用户在机器人可用范围内；给群组发消息需确保机器人在群内且有发言权限。支持文本和富文本消息类型。
### 所需参数
- receive_id：消息接收者的ID，ID类型与receive_id_type一致，必填参数。注意：给用户发消息需确保用户在机器人可用范围内；给群组发消息需确保机器人在群内且有发言权限。
- content：消息内容JSON字符串，必填参数。需根据msg_type设置对应格式，例如：{"text": "你好，我是飞书机器人"}。
- msg_type：消息类型，默认为text。支持：text(文本)、post(富文本)。
- receive_id_type：接收者ID类型，默认为open_id。仅支持open_id类型。

---

## 注意事项
1. 所有工具的app_id和app_secret参数都是可选的，系统会默认从用户配置中自动获取，无需额外传参。
2. 对于时间相关的参数，统一使用"YYYY-MM-DD HH:MM"格式。
3. 所有ID类型参数默认都使用open_id格式。
4. 删除操作（如删除日历、删除日程事件）都是不可逆的，请谨慎使用。

## 飞书应用权限参考
```json
{
  "scopes": {
    "tenant": [
      "calendar:calendar",
      "calendar:calendar.event:create",
      "calendar:calendar.event:read",
      "calendar:calendar.event:update",
      "calendar:calendar:read",
      "calendar:calendar:readonly",
      "contact:contact.base:readonly",
      "contact:user.base:readonly",
      "contact:user.email:readonly",
      "contact:user.employee_id:readonly",
      "contact:user.gender:readonly",
      "contact:user.id:readonly",
      "contact:user.phone:readonly",
      "docs:document.content:read",
      "docx:document",
      "docx:document:create",
      "docx:document:readonly",
      "drive:drive",
      "drive:drive.search:readonly",
      "drive:drive:version:readonly",
      "im:chat:create",
      "im:chat:delete",
      "im:chat:moderation:write_only",
      "im:chat:operate_as_owner",
      "im:chat:read",
      "im:chat:readonly",
      "im:chat:update",
      "im:message",
      "im:message:send_as_bot",
      "space:folder:create"
    ],
    "user": [
      "calendar:calendar",
      "calendar:calendar.event:create",
      "calendar:calendar:read",
      "calendar:calendar:readonly",
      "contact:contact.base:readonly",
      "contact:user.employee_id:readonly",
      "docx:document",
      "drive:drive",
      "drive:drive:readonly",
      "im:chat",
      "im:chat:read",
      "im:chat:readonly",
      "space:document:retrieve"
    ]
  }
}
```