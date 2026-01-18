from fastapi import APIRouter
from app.core.config import settings
# TODO: need to create models 

router = APIRouter(
    prefix="/bingo",
    tags=['ai'], # tags are primarily used for grouping APIs for documentation in swagger
    responses={403: {'description': "N/A"}}
)

from google import genai
from google.genai import types

client = genai.Client(api_key=settings.GOOGLE_AI_STUDIO_API_KEY)


from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    model: str

# TODO: 
# send a single message and get a response
@router.post("/send")
async def send_message(request: ChatRequest) -> dict:
    try:
        response = await client.aio.models.generate_content(
            model=request.model,
            contents=request.message
        )
        return {"message": response.text}
    except Exception as e:
        print(f"Error generating content: {e}")
        return {"message": f"Error: {str(e)}"}

@router.get("/models")
async def get_gemini_models():
    """List available Gemini models."""
    try:
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
            if ("models/gemini" or "models/gemma" in m.name) and not any(forbidden in m.display_name.lower() for forbidden in not_allowed_models):
                gen_models.append(m.name)
                print(m)
        
        return {"models": gen_models}
    except Exception as e:
        print(f"Error fetching models: {e}")
        return {"models": ["models/gemini-1.5-flash-latest"]}

# @router.get("/models")
# def get_models():
#     """List available Gemini models."""
#     try:
#         # Pager object, iterate to get models
#         # This is a broad filter, adjust as needed based on actual SDK response structure
#         all_models = client.models.list()
#         # Simple filtering for 'gemini' models that likely support content generation
#         gemini_models = [
#             m.name for m in all_models 
#             if "gemini" in m.name.lower() and "generateContent" in (m.supported_generation_methods or [])
#         ]
#         return {"models": gemini_models}
#     except Exception as e:
#         print(f"Error fetching models: {e}")
#         # Fallback list if API fails or SDK differs
#         return {"models": ["models/gemini-1.5-flash", "models/gemini-1.5-pro"]}
