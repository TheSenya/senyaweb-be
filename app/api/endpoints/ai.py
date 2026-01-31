from fastapi import APIRouter, Request, HTTPException, Depends

from google.genai import types
import httpx

from pydantic import BaseModel
from app.schemas.ai import OpenRouter

from app.middleware.logger import log_function
from app.api.deps import get_current_admin
from app.models.user import User

# TODO: need to create models 

router = APIRouter(
    prefix="/bingo",
    tags=['ai'],  # tags are primarily used for grouping APIs for documentation in swagger
    responses={403: {'description': "Admin access required"}},
    dependencies=[Depends(get_current_admin)]  # All endpoints in this router require admin
)
class Chat(BaseModel):
    message: str
    model: str
    provider: str = "gemini"

# TODO: 
# send a single message and get a response
@log_function(log_args=True, log_result=True)
@router.post("/send")
async def send_message(request: Request, chat: Chat) -> dict:
    try:
        if chat.provider == "openrouter":
            client = request.app.state.openrouter
            response = client.chat.send(
                model=chat.model,
                messages=[{"role": "user", "content": chat.message}]
            )
            return {"message": response.choices[0].message.content}
        elif chat.provider == "gemini":
            # Default to Gemini
            client = request.app.state.gemini
            response = await client.aio.models.generate_content(
                model=chat.model,
                contents=chat.message
            )
            return {"message": response.text}
        else:
            raise HTTPException(status_code=400, detail=f"Chat provider {chat.provider} not found")
    except Exception as e:
        print(f"Error generating content: {e}")
        return {"message": f"Error: {str(e)}"}

@router.post("/gem_models")
async def get_gemini_models(request: Request):
    """List available Gemini models."""
    try:
        client = request.app.state.gemini
        models = await client.aio.models.list(config={'page_size': 5})
        
        # Async iterator requires specific handling or we list comprehension over 'await' result if it returns list
        # New SDK: list() might return an AsyncPager.
        # We need to iterate it.
        gen_models = []
        not_allowed_models = ['nano', 'robotics', 'image', 'video']

        # TODO: why does this need to be async explain and understand
        # ANSWER: `client.aio` methods are asynchronous. `models.list()` returns an AsyncPager.
        # Iterating over it (`async for`) lazily fetches pages of results from the API over the network.
        # This prevents blocking the event loop while waiting for HTTP responses.
        async for m in models:
            if ("models/gemini" in m.name or "models/gemma" in m.name) and not any(forbidden in m.display_name.lower() for forbidden in not_allowed_models):
                gen_models.append(m.name)
                #print(m)
        
        gen_models.sort()
        return {"models": gen_models}
    except Exception as e:
        print(f"Error fetching models: {e}")
        return {"models": ["models/gemini-1.5-flash-latest"]}

@router.post("/or_models")
async def get_openrouter_models(request: Request): # Need Request object for app state
    try:
        client = request.app.state.openrouter
        # This is now a synchronous method call with the SDK
        res = client.models.list(category="programming")
        
        models_data = []
        for m in res.data:
            pricing = {"prompt": "N/A", "completion": "N/A"}
            # Check for pricing attribute directly or in extra dictionary
            if hasattr(m, 'pricing'):
                 pricing = m.pricing
            
            models_data.append({
                "id": m.id,
                "name": m.name or m.id,
                "pricing": pricing
            })

        models_data.sort(key=lambda x: x['name'])
        return {"models": models_data} 
    except Exception as e:
        print(f"Error fetching OR models: {e}")
        return {"models": []}

@router.post("/credits")
async def get_openrouter_credits(request: Request):
    """Fetch OpenRouter account credits/info."""
    try:
        client = request.app.state.openrouter
        res = client.credits.get_credits()

        credits = res.data
        
        # Map SDK response to our Schema
        # Assuming credits object has 'usage' and 'limit' attributes based on API docs
        print(credits)
        return {"credits": credits}
    except Exception as e:
        print(f"Error fetching credits: {e}")
        # Return empty/zero defaults on error to match schema
        return {"total_usage": 0.0, "total_credits": 0.0}
