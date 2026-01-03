Just for me

--------------
### Packages
--------------
> Core
- fastapi
- uvicorn[standard]

> Configuration & Validation
- pydantic-settings (used to read .env file and maps it to Python classes)

> Database Stack
- sqlalchemy (ORM which allows python to translate python class `models/user.py` instal SQL tables)
- alembic (Git for databases, tracks changes in tables and generates a script to update the actual SQL database without deleting data)
- asyncpg (fastest async driver for for PosgreSQL)

> Dev & Testing
- ruff
- httpx
- pytest

--------------
### Installation Instruction
--------------
`uv venv` to initialize the venv
`uv pip install -r requirements.txt` install all necessary packages

--------------
### Hostings 
--------------
- route 53 for domain name
- cloudflare for tunnel
- route DNS from route 53 to cloudflare