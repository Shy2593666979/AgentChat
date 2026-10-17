import unittest
from contextlib import contextmanager
from unittest.mock import patch

from agentchat.settings import app_settings
from sqlmodel import Session, create_engine, select

app_settings.database = {
    "url": "sqlite:///:memory:",
}
from agentchat.database.dao.llm import LLMDao
from agentchat.database.models.llm import LLMTable
from agentchat.schemas.llm import LLMCreateReq, LLMUpdateReq


class ModelDisplayNameTests(unittest.IsolatedAsyncioTestCase):

    async def test_create_update_clear_display_name_without_changing_connection(self):
        engine=create_engine("sqlite:///:memory:")
        LLMTable.__table__.create(engine)
        @contextmanager
        def isolated_session():
            with Session(engine) as session: yield session
        with patch("agentchat.database.dao.llm.session_getter",isolated_session):
            await LLMDao.create_llm(model="ep-real-model",show_model=" 豆包 Pro ",base_url="https://example.com",llm_type="LLM",api_key="test-only",provider="火山引擎",user_id="test")
            with Session(engine) as session: model=session.exec(select(LLMTable)).one();model_id=model.llm_id
            await LLMDao.update_llm(llm_id=model_id,show_model="豆包助手")
            await LLMDao.update_llm(llm_id=model_id,provider="火山")
            with Session(engine) as session:
                model=session.get(LLMTable,model_id)
                self.assertEqual(model.show_model,"豆包助手")
                self.assertEqual(model.model,"ep-real-model")
                self.assertEqual(model.api_key,"test-only")
            await LLMDao.update_llm(llm_id=model_id,show_model="")
            with Session(engine) as session: self.assertEqual(session.get(LLMTable,model_id).show_model,"")
        engine.dispose()

    def test_old_requests_remain_compatible(self):
        req=LLMCreateReq(model="real",api_key="test",base_url="https://example.com")
        self.assertEqual(req.show_model,"")
        self.assertIsNone(LLMUpdateReq(llm_id="test").show_model)

if __name__ == "__main__": unittest.main()
