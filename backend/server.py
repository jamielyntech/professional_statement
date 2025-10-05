from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
from emergentintegrations.llm.chat import LlmChat, UserMessage
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Mystical Whispers Comics API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class ComicPanel(BaseModel):
    panel: int
    scene: str
    dialogue: str
    character_actions: Optional[str] = None
    mood: Optional[str] = None

class StoryRequest(BaseModel):
    story: str
    title: Optional[str] = None

class StoryboardResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    panels: List[ComicPanel]
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Comic(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    panels: List[ComicPanel]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    story_text: str

# Initialize LLM Chat
def get_llm_chat():
    return LlmChat(
        api_key=os.environ['EMERGENT_LLM_KEY'],
        session_id="mystical-comics",
        system_message="You are the Storyboard Parser for Mystical Whispers Comics. Take the user's story and divide it into 3–6 clear panels. Each panel should include: scene description (setting, mood), character actions (focusing on Jamie and Kylee when mentioned, or other characters as appropriate), and dialogue or narration text. Return ONLY a valid JSON array formatted like: [{'panel': 1, 'scene': '...', 'dialogue': '...', 'character_actions': '...', 'mood': '...'}]. Do not include any other text or explanations."
    ).with_model("openai", "gpt-4o-mini")

# Routes
@api_router.get("/")
async def root():
    return {"message": "Welcome to Mystical Whispers Comics API!"}

@api_router.post("/parse-story", response_model=StoryboardResponse)
async def parse_story(request: StoryRequest):
    try:
        # Initialize LLM chat
        chat = get_llm_chat()
        
        # Create user message
        story_prompt = f"Parse this story into comic panels: {request.story}"
        user_message = UserMessage(text=story_prompt)
        
        # Get response from LLM
        response = await chat.send_message(user_message)
        
        # Parse JSON response
        try:
            panels_data = json.loads(response)
            panels = [ComicPanel(**panel_data) for panel_data in panels_data]
        except json.JSONDecodeError:
            # If JSON parsing fails, create a simple fallback
            panels = [
                ComicPanel(
                    panel=1,
                    scene="A mystical setting where the story unfolds",
                    dialogue=request.story[:200] + "..." if len(request.story) > 200 else request.story,
                    character_actions="Characters begin their journey",
                    mood="Mysterious and enchanting"
                )
            ]
        
        # Create storyboard response
        storyboard = StoryboardResponse(
            title=request.title or "Untitled Story",
            panels=panels
        )
        
        # Save to database
        comic_dict = Comic(
            title=storyboard.title,
            panels=storyboard.panels,
            story_text=request.story
        ).dict()
        
        await db.comics.insert_one(comic_dict)
        
        return storyboard
        
    except Exception as e:
        logging.error(f"Error parsing story: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to parse story: {str(e)}")

@api_router.get("/comics", response_model=List[Comic])
async def get_comics():
    try:
        comics = await db.comics.find().to_list(100)
        return [Comic(**comic) for comic in comics]
    except Exception as e:
        logging.error(f"Error fetching comics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch comics")

@api_router.get("/comics/{comic_id}", response_model=Comic)
async def get_comic(comic_id: str):
    try:
        comic = await db.comics.find_one({"id": comic_id})
        if not comic:
            raise HTTPException(status_code=404, detail="Comic not found")
        return Comic(**comic)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching comic: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch comic")

@api_router.delete("/comics/{comic_id}")
async def delete_comic(comic_id: str):
    try:
        result = await db.comics.delete_one({"id": comic_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Comic not found")
        return {"message": "Comic deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting comic: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete comic")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
