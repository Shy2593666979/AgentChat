import unittest
from contextlib import contextmanager
from unittest.mock import patch

from agentchat.settings import app_settings
from sqlmodel import Session, create_engine

app_settings.database = {
    "url": "sqlite:///:memory:",
}
from agentchat.database.dao.user import UserDao
from agentchat.database.models.user import UserTable


class UserAvatarTests(unittest.TestCase):
    def test_upload_clear_and_omitted_avatar_roundtrip(self):
        # 隔离数据库，验证恢复字母头像确实清空图片地址，省略头像则保留。
        engine = create_engine("sqlite:///:memory:")
        UserTable.__table__.create(engine)
        with Session(engine) as session:
            session.add(UserTable(user_id="avatar-test", user_name="Test", user_email="test@example.com", user_password="test", user_avatar="old.png"))
            session.commit()
        @contextmanager
        def isolated_session():
            with Session(engine) as session:
                yield session
        with patch("agentchat.database.dao.user.session_getter", isolated_session):
            UserDao.update_user_info("avatar-test", "https://example.com/upload.png", "简介")
            self.assertEqual(UserDao.get_user("avatar-test").user_avatar, "https://example.com/upload.png")
            UserDao.update_user_info("avatar-test", None, "新简介")
            self.assertEqual(UserDao.get_user("avatar-test").user_avatar, "https://example.com/upload.png")
            UserDao.update_user_info("avatar-test", "", "新简介")
            self.assertEqual(UserDao.get_user("avatar-test").user_avatar, "")
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
