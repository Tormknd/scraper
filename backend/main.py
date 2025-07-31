from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
from scraper import scrape
import asyncio
from pathlib import Path

app = FastAPI(title="Scraper-LLM API")

# Serve static files from images directory
images_dir = Path(__file__).parent / "images"
images_dir.mkdir(exist_ok=True)
app.mount("/images", StaticFiles(directory=images_dir), name="images")

class Req(BaseModel):
    url: HttpUrl

@app.post("/scrape")
async def scrape_endpoint(payload: Req):
    try:
        # Run the scraping in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, scrape, str(payload.url))
        return data
    except Exception as e:
        import traceback
        print(f"Error in scrape endpoint: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e)) 