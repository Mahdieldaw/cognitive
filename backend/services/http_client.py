import httpx

# Use an async client for FastAPI
client = httpx.AsyncClient(timeout=60.0)