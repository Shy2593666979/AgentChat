import sys
sys.path.append("..")
from typing import Optional
from uuid import uuid4
from sqlmodel import Field, SQLModel, create_engine, Session
from database.models import HistoryTable, DialogTable
from sqlalchemy import  select

mysql_url = "mysql+pymysql://root:mingguang0703@localhost:3306/agentchat"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_name: str
    encrypted_password: str
    age: Optional[int] = Field(default=None)
    
engine = create_engine(mysql_url)
SQLModel.metadata.create_all(engine)

u1 = User(user_name="熊大1", encrypted_password="askklklasdo1", age=12)
u2 = User(user_name="熊大2", encrypted_password="askklklasdo1", age=14)
u3 = User(user_name="熊大3", encrypted_password="askklklasdo1", age=16)
with Session(engine) as session:
    session.add(u1)
    session.add(u2)
    session.add(u3)
    session.commit()

def sss():
    with Session(engine) as session:
        sql = select(User)
        result = session.exec(sql).all()
        return result

result = sss()
final = []
for data in result:
    final.append(data[0])

print(final[0].id)