from sqlmodel import SQLModel, Field

# Create models here
# class Item(SQLModel, table=True):
#     id: int | None = Field(default=None, primary_key=True)
#     name: str

class RequestInfoMixin(SQLModel):
    user_agent: str = Field(default="Unknown")
    ip_address: str = Field(default="Unknown")

