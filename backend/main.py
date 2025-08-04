from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from scraper import scrape, analyze_website, extract_data_with_requirements, chat_message, get_conversation_history, get_help_info
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
import uuid
import os
import time

app = FastAPI(
    title="Scraper-LLM API - Version Conversationnelle",
    description="Real-time web scraping and AI-powered data extraction API",
    version="2.0.0"
)

# Production CORS configuration
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://your-frontend-domain.vercel.app",  # Replace with your Vercel domain
    "https://your-frontend-domain.netlify.app",  # Replace with your Netlify domain
    "*"  # For development - remove in production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from images directory
images_dir = Path(__file__).parent / "images"
images_dir.mkdir(exist_ok=True)
app.mount("/images", StaticFiles(directory=images_dir), name="images")

class ScrapeRequest(BaseModel):
    url: HttpUrl

class AnalyzeRequest(BaseModel):
    url: HttpUrl
    session_id: Optional[str] = None

class ExtractRequest(BaseModel):
    requirements: str
    session_id: str

class ChatRequest(BaseModel):
    message: str
    session_id: str

class SessionResponse(BaseModel):
    session_id: str
    message: str

class AnalysisResponse(BaseModel):
    success: bool
    analysis: Optional[Dict[str, Any]] = None
    ai_response: str
    session_id: str
    error: Optional[str] = None

class ExtractionResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    ai_response: str
    error: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

class HistoryResponse(BaseModel):
    session_id: str
    history: List[Dict[str, str]]

@app.post("/scrape", response_model=Dict)
async def scrape_endpoint(payload: ScrapeRequest):
    start_time = time.time()
    try:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, scrape, str(payload.url))
        processing_time = time.time() - start_time
        data["processing_time"] = f"{processing_time:.2f}s"
        return data
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_website_endpoint(payload: AnalyzeRequest):
    start_time = time.time()
    try:
        session_id = payload.session_id or str(uuid.uuid4())
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, analyze_website, session_id, str(payload.url))
        
        processing_time = time.time() - start_time
        result["processing_time"] = f"{processing_time:.2f}s"
        
        return AnalysisResponse(
            success=result["success"],
            analysis=result.get("analysis"),
            ai_response=result["ai_response"],
            session_id=session_id,
            error=result.get("error")
        )
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract", response_model=ExtractionResponse)
async def extract_data_endpoint(payload: ExtractRequest):
    start_time = time.time()
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, extract_data_with_requirements, payload.session_id, payload.requirements)
        
        processing_time = time.time() - start_time
        result["processing_time"] = f"{processing_time:.2f}s"
        
        return ExtractionResponse(
            success=result["success"],
            data=result.get("data"),
            ai_response=result.get("ai_response", "No AI response available"),
            error=result.get("error")
        )
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    start_time = time.time()
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, chat_message, payload.session_id, payload.message)
        
        processing_time = time.time() - start_time
        
        return ChatResponse(
            response=response,
            session_id=payload.session_id
        )
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{session_id}", response_model=HistoryResponse)
async def get_history_endpoint(session_id: str):
    try:
        loop = asyncio.get_event_loop()
        history = await loop.run_in_executor(None, get_conversation_history, session_id)
        
        return HistoryResponse(
            session_id=session_id,
            history=history
        )
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/session/new", response_model=SessionResponse)
async def create_session_endpoint():
    try:
        session_id = str(uuid.uuid4())
        
        from scraper import create_conversation_session
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, create_conversation_session, session_id)
        
        return SessionResponse(
            session_id=session_id,
            message="Nouvelle session créée avec succès"
        )
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {
        "message": "Scraper-LLM API - Version Conversationnelle",
        "version": "2.0.0",
        "status": "running",
        "deployment": "render",
        "real_time": True,
        "capabilities": {
            "basic_scraping": True,
            "advanced_scraping": "check_availability",
            "ai_extraction": True,
            "image_download": True
        },
        "endpoints": {
            "/scrape": "POST - Extraction legacy (compatibilité)",
            "/analyze": "POST - Analyse un site web",
            "/extract": "POST - Extrait des données selon les exigences",
            "/chat": "POST - Chat simple avec l'IA",
            "/history/{session_id}": "GET - Historique de conversation",
            "/session/new": "POST - Crée une nouvelle session",
            "/help": "GET - Aide et commandes disponibles",
            "/health": "GET - Health check",
            "/capabilities": "GET - Check available features"
        },
        "usage": {
            "1. Créer une session": "POST /session/new",
            "2. Analyser un site": "POST /analyze avec URL",
            "3. Spécifier les besoins": "POST /chat avec vos exigences",
            "4. Extraire les données": "POST /extract avec les exigences"
        }
    }

@app.get("/help")
async def help_endpoint():
    try:
        loop = asyncio.get_event_loop()
        help_info = await loop.run_in_executor(None, get_help_info)
        
        return {
            "message": "Aide - Scraper-LLM Commands",
            "commands": help_info["commands"],
            "examples": help_info["examples"],
            "workflow": {
                "1. Analyser": "Commencez par analyser un site avec 'analyze <url>'",
                "2. Consulter": "L'IA vous dira quel type de données sont disponibles",
                "3. Extraire": "Utilisez 'extract <requirements>' avec des exigences spécifiques",
                "4. Chat": "Posez des questions avec 'chat <message>' pour obtenir de l'aide"
            }
        }
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test-image/{filename}")
async def test_image_endpoint(filename: str):
    try:
        image_path = images_dir / filename
        if image_path.exists():
            return {"status": "success", "message": f"Image {filename} exists", "path": str(image_path)}
        else:
            return {"status": "error", "message": f"Image {filename} not found", "available": [f.name for f in images_dir.iterdir() if f.is_file()]}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "deployment": "render",
        "real_time": True,
        "uptime": "running"
    }

@app.get("/capabilities")
async def capabilities_check():
    capabilities = {
        "basic_scraping": True,
        "ai_extraction": True,
        "image_download": True,
        "advanced_scraping": False,
        "playwright": False,
        "selenium": False,
        "newspaper3k": False
    }
    
    try:
        import playwright
        capabilities["playwright"] = True
    except ImportError:
        pass
    
    try:
        import selenium
        capabilities["selenium"] = True
    except ImportError:
        pass
    
    try:
        import newspaper
        capabilities["newspaper3k"] = True
    except ImportError:
        pass
    
    if capabilities["playwright"] or capabilities["selenium"] or capabilities["newspaper3k"]:
        capabilities["advanced_scraping"] = True
    
    return {
        "api_version": "2.0.0",
        "deployment_platform": "render",
        "real_time_enabled": True,
        "auto_scaling": True,
        "health_checks": True,
        "live_logs": True,
        "capabilities": capabilities
    }

@app.get("/metrics")
async def metrics():
    return {
        "api_version": "2.0.0",
        "deployment_platform": "render",
        "real_time_enabled": True,
        "auto_scaling": True,
        "health_checks": True,
        "live_logs": True
    }

# Production server configuration
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 