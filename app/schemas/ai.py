from pydantic import BaseModel

class OpenRouter(BaseModel):
    
    class Credits(BaseModel):
        total_credits: float
        total_usage: float