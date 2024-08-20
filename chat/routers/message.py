from fastapi import APIRouter, Request
from database.base import MessageLike, MessageDown
from type.schemas import resp_200, resp_500

router = APIRouter()

@router.post("/message/like")
async def insert_message_like(request: Request):
    body = await request.json()

    userInput = body.get('userInput')
    agentOutput = body.get('agentOutput')
    MessageLike.create_message_like(userInput=userInput, agentOutput=agentOutput)

    return resp_200()

@router.post("/message/down")
async def insert_message_down(request: Request):
    body = await request.json()

    userInput = body.get('userInput')
    agentOutput = body.get('agentOutput')
    MessageDown.create_message_down(userInput=userInput, agentOutput=agentOutput)

    return resp_200()