The `FastAPI()` class is the heart of your application. When you instantiate it, you are configuring the entire behavior of your API, from how it looks in documentation to how it handles errors and routing behind the scenes.

Here is a deep dive into the parameters you can pass to `FastAPI(...)`, grouped by their purpose.

-----

### 1\. API Metadata (Documentation Appearance)

These parameters control what users see when they visit your automatic documentation page (`/docs`). They are crucial for professionalizing your API.

  * **`title`** (`str`): The large heading at the top of the documentation.
  * **`description`** (`str`): A detailed explanation of your API. You can use **Markdown** here (bolding, lists, links).
  * **`version`** (`str`): The version of your API (e.g., `2.5.0`).
  * **`summary`** (`str`): A short summary (available in OpenAPI 3.1.0+) that appears right under the title, smaller than the description.
  * **`terms_of_service`** (`str`): A URL to your terms of service.
  * **`contact`** (`dict`): Contact info for the API maintainer (name, url, email).
  * **`license_info`** (`dict`): License details (name, identifier, url).

**Example:**

```python
app = FastAPI(
    title="SuperNova API",
    summary="High-performance astronomical data.",
    description="""
    ## Usage
    This API allows you to query **supernova** data.
    * Use `/stars` for star data.
    * Use `/planets` for planet data.
    """,
    version="1.0.0",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Support Team",
        "url": "http://x-force.example.com/contact/",
        "email": "dp@x-force.example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)
```

-----

### 2\. Documentation URLs (Customizing Paths)

By default, FastAPI serves docs at `/docs` and `/redoc`. You can change these locations or disable them entirely (useful for production security).

  * **`docs_url`** (`str` | `None`): The path for the Swagger UI. Set to `None` to disable it.
  * **`redoc_url`** (`str` | `None`): The path for the alternative ReDoc UI.
  * **`openapi_url`** (`str` | `None`): The path where the raw `openapi.json` file is served. This file drives the UI. If you disable this, *all* documentation interfaces will stop working.

**Example (Hiding docs for security):**

```python
app = FastAPI(
    docs_url="/secret-docs", # Move docs to a hidden path
    redoc_url=None,          # Disable ReDoc entirely
    openapi_url="/api/v1/openapi.json" # Move the JSON schema
)
```

-----

### 3\. Global Execution Logic

These parameters affect how the application runs and processes requests.

  * **`lifespan`** (`func`): The modern way to handle logic that runs **before** the app starts (connecting to DBs) and **after** it stops (closing connections). It replaces the old `on_startup` and `on_shutdown` lists.
  * **`dependencies`** (`list`): A list of dependencies that apply to **every single endpoint** in the application. Useful for global authentication (e.g., "deny access to the entire app if no API key").
  * **`default_response_class`**: By default, FastAPI returns JSON (`JSONResponse`). You can change this to `ORJSONResponse` (a faster JSON library) or `HTMLResponse` if you are building a website, not an API.
  * **`redirect_slashes`** (`bool`): Defaults to `True`. If a user visits `/items` but the path is `/items/`, FastAPI redirects them automatically.

**Example:**

```python
from fastapi.responses import ORJSONResponse

async def verify_api_key(token: str):
    if token != "secret":
        raise HTTPException(403)

app = FastAPI(
    lifespan=my_lifespan_function,
    dependencies=[Depends(verify_api_key)], # Locks the WHOLE app
    default_response_class=ORJSONResponse    # Makes all responses faster
)
```

-----

### 4\. OpenAPI Customization (Advanced)

These allow you to fine-tune the generated OpenAPI schema (the standard that describes your API).

  * **`openapi_tags`** (`list[dict]`): Adds metadata to the tags used in your routes. You can add descriptions or external links to specific sections of your docs.
  * **`servers`** (`list[dict]`): Lets you list different servers in your documentation (e.g., "Production", "Staging", "Local"). This adds a dropdown menu in Swagger UI.
  * **`swagger_ui_parameters`** (`dict`): Configures the look and feel of the Swagger UI itself (e.g., expanding all tags by default, or hiding the "Try it out" button).

**Example:**

```python
tags_metadata = [
    {
        "name": "users",
        "description": "Operations with users. The **login** logic is also here.",
    },
    {
        "name": "items",
        "description": "Manage items. So _fancy_ they have their own docs.",
        "externalDocs": {
            "description": "Items external docs",
            "url": "https://fastapi.tiangolo.com/",
        },
    },
]

app = FastAPI(
    openapi_tags=tags_metadata,
    servers=[
        {"url": "https://api.example.com", "description": "Production Server"},
        {"url": "https://staging.example.com", "description": "Staging Environment"}
    ],
    swagger_ui_parameters={"defaultModelsExpandDepth": -1} # Hides the "Schemas" section at bottom
)
```

-----

### 5\. Proxy & Network Configuration

Crucial when your application is running behind a proxy like **Nginx**, **Traefik**, or AWS Load Balancer.

  * **`root_path`** (`str`): If your API is hosted at `https://example.com/api/v1`, but your application code thinks it is at `/`, the documentation will break because it tries to fetch `/openapi.json` instead of `/api/v1/openapi.json`.
      * Setting `root_path="/api/v1"` tells FastAPI, "Even though I am running locally, pretend I am sitting at this subpath."

**Example:**

```python
# Use this if Nginx strips the "/api/v1" prefix before forwarding the request
app = FastAPI(root_path="/api/v1")
```

-----

### 6\. Debugging

  * **`debug`** (`bool`): Defaults to `False`.
      * If `True`, any unhandled exception (like a coding error) will show a **traceback** in the response instead of "Internal Server Error".
      * **WARNING:** Never use `debug=True` in production, as it exposes your code structure to attackers.

-----

### Summary Table

| Parameter | Category | Use Case |
| :--- | :--- | :--- |
| `title`, `description`, `version` | Metadata | Professionalizing the `/docs` page. |
| `docs_url`, `redoc_url` | URLs | Hiding docs or moving them to `/documentation`. |
| `dependencies` | Logic | Securing the **entire** API with one line. |
| `lifespan` | Logic | Connecting to DB on startup / closing on shutdown. |
| `default_response_class` | Performance | Switching to `ORJSONResponse` for speed. |
| `servers` | OpenAPI | Showing "Production" vs "Staging" dropdowns in docs. |
| `root_path` | Network | Fixing docs when running behind Nginx/AWS ALB. |