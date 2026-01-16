from fastapi import APIRouter
from typing import str

router = APIRouter(
    prefix="/bingo",
    tags=['ai'] # tags are primarily used for grouping APIs for documentation in swagger
    responses={403: {'description': "N/A"}}
)

models = {'gemini'}

# start a chat session
@router.post('/start')
async def start_chat(who: str) -> chat_id: str:

# send a chat message to the model
@router.post("/send")
async def send_message(message: str):
    return {"message": message}

# get chat history
@router.get("/history")
aysnc def get_history()

