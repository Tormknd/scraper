# Scraper Backend

FastAPI backend for web scraping using OpenAI LLM.

## Setup

1. Create virtual environment:
```bash
python -m venv .venv
```

2. Activate virtual environment:
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Copy the example file
cp env.example .env

# Edit .env and add your OpenAI API key
OPENAI_API_KEY=sk-your-actual-api-key-here
```

## Running the server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### POST /scrape

Scrapes a website and extracts product information using OpenAI.

**Request:**
```json
{
  "url": "https://books.toscrape.com/"
}
```

**Response:**
```json
{
  "items": [
    {
      "title": "Sharp Objects",
      "price": "£47.82",
      "img": "https://books.toscrape.com/...jpg",
      "img_local": "images/51s6B58.png"
    }
  ]
}
```

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc` 