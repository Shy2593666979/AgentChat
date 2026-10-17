import unittest

from agentchat.schemas.completion import CompletionReq
from agentchat.settings import app_settings
from agentchat.utils.chat_attachments import attachment_events
from sqlmodel import Session, create_engine, select

app_settings.database = {
    "url": "sqlite:///:memory:",
}
from agentchat.database.models.history import HistoryTable


class AttachmentTests(unittest.TestCase):
    def test_metadata_survives_history_roundtrip(self):
        req=CompletionReq(conversation_id="test",user_input="检查附件",file_url="https://example.com/upload/abc.docx",file_name="项目说明.docx",file_size=2048,file_type="application/test")
        engine=create_engine("sqlite:///:memory:")
        HistoryTable.__table__.create(engine)
        with Session(engine) as session:
            session.add(HistoryTable(conversation_id="test",role="user",content=req.user_input,events=attachment_events(req)))
            session.commit()
        with Session(engine) as session:
            data=session.exec(select(HistoryTable)).one().to_dict()
            self.assertEqual(
                data["events"][0]["data"],
                {
                    "url": req.file_url,
                    "name": req.file_name,
                    "size": 2048,
                    "mime": "application/test",
                },
            )
        engine.dispose()
    def test_legacy_request_and_no_attachment(self):
        self.assertEqual(attachment_events(CompletionReq(conversation_id="test",user_input="你好")),[])
        data=attachment_events(CompletionReq(conversation_id="test",user_input="检查",file_url="https://example.com/%E6%96%87%E4%BB%B6.pdf"))[0]["data"]
        self.assertEqual(data["name"],"文件.pdf")
        self.assertNotIn("size",data)

if __name__ == "__main__": unittest.main()
