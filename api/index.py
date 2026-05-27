from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import traceback
import sys
import os

app = FastAPI(title="Gemini Live API Server")

try:
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware
    import datetime
    import warnings

    # Suppress warnings
    warnings.filterwarnings("ignore", message=".*The SDK's token creation implementation is experimental.*")

    from google import genai
    from dotenv import load_dotenv

    # Try importing memory engine (lazy init)
    try:
        from memory_engine import AURAMemoryEngine
        memory_engine = AURAMemoryEngine()
        HAS_MEMORY = True
    except Exception as e:
        print(f"Memory Engine failed to load: {e}")
        HAS_MEMORY = False

    load_dotenv()

    # Allow CORS for local dev
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

    if not GEMINI_API_KEY:
        print("⚠️ Warning: GEMINI_API_KEY not found in environment.")
        try:
            client = genai.Client(http_options={"api_version": "v1alpha"})
        except Exception as e:
            print(f"Failed to initialize Gemini Client: {e}")
            client = None
    else:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY, http_options={"api_version": "v1alpha"})
        except Exception as e:
            print(f"Failed to initialize Gemini Client with key: {e}")
            client = None

    @app.post("/api/token")
    async def get_ephemeral_token(request: Request):
        """Generates an ephemeral token for the Gemini Live API."""
        if not client:
            return JSONResponse(status_code=500, content={"error": "Gemini Client not initialized. Check GEMINI_API_KEY environment variable."})
            
        try:
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

            return {"token": token.name, "expires_at": expire_time.isoformat()}
        except Exception as e:
            print(f"Error generating ephemeral token: {e}")
            return JSONResponse(status_code=500, content={"error": str(e)})

    @app.post("/api/memory/search")
    async def search_memory_api(request: Request):
        """API endpoint to search the AURA persistent memory"""
        if not HAS_MEMORY:
            return JSONResponse(status_code=503, content={"error": "Memory engine disabled"})
            
        try:
            data = await request.json()
            query = data.get("query", "")
            filter_type = data.get("filter_type")
            top_k = data.get("top_k", 5)
            
            results = memory_engine.retrieve_context(query, top_k=top_k, filter_type=filter_type)
            return {"memories": results}
        except Exception as e:
            print(f"Error searching memory: {e}")
            return JSONResponse(status_code=500, content={"error": str(e)})

    @app.post("/api/memory/store")
    async def store_memory_api(request: Request):
        """API endpoint to store data into AURA persistent memory"""
        if not HAS_MEMORY:
            return JSONResponse(status_code=503, content={"error": "Memory engine disabled"})
            
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
                return JSONResponse(status_code=400, content={"error": "Invalid memory type"})
                
            return {"status": "success"}
        except Exception as e:
            print(f"Error storing memory: {e}")
            return JSONResponse(status_code=500, content={"error": str(e)})

    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
    if os.path.exists(frontend_dir):
        try:
            app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")
        except Exception as e:
            print(f"Error mounting static files: {e}")

except Exception as fatal_error:
    error_trace = traceback.format_exc()
    print(f"FATAL STARTUP ERROR:\n{error_trace}")
    
    @app.get("/{path:path}")
    @app.post("/{path:path}")
    async def catch_all_error(path: str):
        return JSONResponse(
            status_code=500, 
            content={
                "error": "Backend crashed during startup on Vercel",
                "details": str(fatal_error),
                "traceback": error_trace.split("\n")
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.index:app", host="0.0.0.0", port=8000)
