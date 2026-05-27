#!/usr/bin/env python3
"""Server for Gemini Live API with Ephemeral Tokens
Provides an endpoint to generate ephemeral tokens and serves static files.
"""

import asyncio
import json
import mimetypes
import os
import datetime
import warnings

# Suppress the experimental token creation warning from the SDK
warnings.filterwarnings("ignore", message=".*The SDK's token creation implementation is experimental.*")

from aiohttp import web
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Try importing memory engine (lazy init)
try:
    from memory_engine import AURAMemoryEngine
    memory_engine = AURAMemoryEngine()
    HAS_MEMORY = True
except Exception as e:
    print(f"Memory Engine failed to load: {e}")
    HAS_MEMORY = False

# Load environment variables from .env file
load_dotenv()

# Configuration
HTTP_PORT = 8000  # Port for HTTP server
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Initialize the Gemini GenAI client
if not GEMINI_API_KEY:
    print("⚠️ Warning: GEMINI_API_KEY not found in environment. Please set it in .env or as an environment variable.")
    # Fallback to default client which might pick up GOOGLE_API_KEY
    client = genai.Client(http_options={"api_version": "v1alpha"})
else:
    client = genai.Client(api_key=GEMINI_API_KEY, http_options={"api_version": "v1alpha"})


async def get_ephemeral_token(request):
    """Generates an ephemeral token for the Gemini Live API."""
    try:
        # Optional: Allow client to pass an API key
        # data = await request.json()
        # api_key = data.get("api_key")
        # if api_key:
        #     local_client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})
        # else:
        #     local_client = client

        now = datetime.datetime.now(tz=datetime.timezone.utc)
        expire_time = now + datetime.timedelta(minutes=30)
        
        # Create an ephemeral token
        token = client.auth_tokens.create(
            config={
                "uses": 1,
                "expire_time": expire_time.isoformat(),
                "new_session_expire_time": (now + datetime.timedelta(minutes=1)).isoformat(),
                "http_options": {"api_version": "v1alpha"},
            }
        )

        return web.json_response({
            "token": token.name,
            "expires_at": expire_time.isoformat()
        })
    except Exception as e:
        print(f"Error generating ephemeral token: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def search_memory_api(request):
    """API endpoint to search the AURA persistent memory"""
    if not HAS_MEMORY:
        return web.json_response({"error": "Memory engine disabled"}, status=503)
        
    try:
        data = await request.json()
        query = data.get("query", "")
        filter_type = data.get("filter_type")
        top_k = data.get("top_k", 5)
        
        results = memory_engine.retrieve_context(query, top_k=top_k, filter_type=filter_type)
        return web.json_response({"memories": results})
    except Exception as e:
        print(f"Error searching memory: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def store_memory_api(request):
    """API endpoint to store data into AURA persistent memory"""
    if not HAS_MEMORY:
        return web.json_response({"error": "Memory engine disabled"}, status=503)
        
    try:
        data = await request.json()
        memory_type = data.get("type")
        
        if memory_type == "conversation":
            memory_engine.store_conversation(
                user_msg=data.get("user_message", ""),
                ai_response=data.get("ai_message", "")
            )
        elif memory_type == "screen":
            memory_engine.store_screen_observation(
                ocr_text=data.get("ocr_text", ""),
                app_name=data.get("app_name", "Unknown App"),
                window_title=data.get("window_title", "")
            )
        elif memory_type == "task":
            memory_engine.store_task_context(
                task_description=data.get("description", "")
            )
        else:
            return web.json_response({"error": "Invalid memory type"}, status=400)
            
        return web.json_response({"status": "success"})
    except Exception as e:
        print(f"Error storing memory: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def serve_static_file(request):
    """Serve static files from the frontend directory."""
    path = request.match_info.get("path", "index.html")

    # Security: prevent directory traversal
    path = path.lstrip("/")
    if ".." in path:
        return web.Response(text="Invalid path", status=400)

    # Default to index.html
    if not path or path == "/":
        path = "index.html"

    # Get the full file path - serve from frontend folder
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    file_path = os.path.join(frontend_dir, path)

    # Check if file exists
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return web.Response(text="File not found", status=404)

    # Determine content type
    content_type, _ = mimetypes.guess_type(file_path)
    if file_path.endswith('.css'):
        content_type = "text/css"
    elif file_path.endswith('.js'):
        content_type = "application/javascript"
    if content_type is None:
        content_type = "application/octet-stream"

    # Read and serve the file
    try:
        with open(file_path, "rb") as f:
            content = f.read()
        return web.Response(body=content, content_type=content_type)
    except Exception as e:
        print(f"Error serving file {path}: {e}")
        return web.Response(text="Internal server error", status=500)


async def main():
    """Starts the HTTP server."""
    app = web.Application()
    
    # API endpoints
    app.router.add_post("/api/token", get_ephemeral_token)
    app.router.add_post("/api/memory/search", search_memory_api)
    app.router.add_post("/api/memory/store", store_memory_api)
    
    # Static files
    app.router.add_get("/", serve_static_file)
    app.router.add_get("/{path:.*}", serve_static_file)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", HTTP_PORT)
    await site.start()
    
    print(f"""
+------------------------------------------------------------+
|     Gemini Live API Server (Ephemeral Token Approach)      |
+------------------------------------------------------------+
|                                                            |
|  Web Interface: http://localhost:{HTTP_PORT:<5}                   |
|  API Endpoint:  POST /api/token                         |
|                                                            |
|  Instructions:                                             |
|  1. Ensure GEMINI_API_KEY is set in your environment       |
|  2. Open http://localhost:{HTTP_PORT} in your browser              |
|  3. Click Connect to start!                                |
|                                                            |
+------------------------------------------------------------+
""")
    
    # Keep the server running
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
