from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
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
from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
import json
import base64
import io
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np

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
    image_url: Optional[str] = None
    image_base64: Optional[str] = None

class StoryRequest(BaseModel):
    story: str
    title: Optional[str] = None
    style: Optional[str] = "Mystical Watercolor"
    aspect_ratio: Optional[str] = "4:5"
    generate_images: Optional[bool] = True

class StoryboardResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    panels: List[ComicPanel]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    style: str = "Mystical Watercolor"
    aspect_ratio: str = "4:5"

class Comic(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    panels: List[ComicPanel]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    story_text: str
    style: str = "Mystical Watercolor"
    aspect_ratio: str = "4:5"

class CharacterReference(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    image_base64: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Initialize LLM Chat
def get_llm_chat():
    return LlmChat(
        api_key=os.environ['EMERGENT_LLM_KEY'],
        session_id="mystical-comics",
        system_message="""You are the Storyboard Parser for Mystical Whispers Comics. 
        
        Take the user's story and divide it into 5–10 clear panels for a detailed comic strip. Each panel should include:
        - panel: number (1, 2, 3, etc.)
        - scene: detailed visual description for AI image generation (include setting, lighting, mood, visual elements)
        - dialogue: speech, narration, or text for this panel
        - character_actions: what characters are doing (focus on Jamie and Kylee when mentioned)
        - mood: the emotional atmosphere
        
        IMPORTANT: Return ONLY a valid JSON array with no additional text. Format exactly like this:
        [{
          "panel": 1,
          "scene": "Jamie and Kylee stand before an ornate mirror in their grandmother's dusty attic, golden light emanating from its surface, dust particles floating in magical beams of light, warm amber lighting",
          "dialogue": "Look Kylee, the mirror is glowing!",
          "character_actions": "Jamie points excitedly at the magical mirror while Kylee steps closer with wonder",
          "mood": "Mysterious and exciting"
        }]
        
        Make scene descriptions rich and detailed for AI image generation. Do not include any explanations, markdown formatting, or extra text."""
    ).with_model("openai", "gpt-4o-mini")

# Initialize Image Generation
def get_image_generator():
    return OpenAIImageGeneration(api_key=os.environ['EMERGENT_LLM_KEY'])

# Helper functions
async def generate_panel_image(panel: ComicPanel, style: str = "Mystical Watercolor", jamie_desc: str = "", kylee_desc: str = ""):
    """Generate an AI image for a comic panel"""
    try:
        image_gen = get_image_generator()
        
        # Create detailed prompt
        character_context = ""
        if "jamie" in panel.scene.lower() or (panel.character_actions and "jamie" in panel.character_actions.lower()):
            character_context += f" Jamie: {jamie_desc}."
        if "kylee" in panel.scene.lower() or (panel.character_actions and "kylee" in panel.character_actions.lower()):
            character_context += f" Kylee: {kylee_desc}."
        
        prompt = f"""{panel.scene}. {panel.character_actions or ''}. {character_context}
        
        Art style: {style}
        Mood: {panel.mood}
        Color palette: Mystical - magenta #e74285, teal #20b69e, gold #fcd94c, midnight navy #1a1330
        Add watercolor glow effects and magical atmosphere.
        Comic book illustration style, detailed and vibrant."""
        
        # Generate image with simpler call
        try:
            images = await image_gen.generate_images(
                prompt=prompt,
                number_of_images=1
            )
        except Exception as img_error:
            logging.warning(f"Image generation failed for panel {panel.panel}, trying with dall-e-3: {img_error}")
            # Fallback to dall-e-3
            images = await image_gen.generate_images(
                prompt=prompt,
                model="dall-e-3",
                number_of_images=1
            )
        
        if images and len(images) > 0:
            # Convert to base64
            image_base64 = base64.b64encode(images[0]).decode('utf-8')
            return image_base64
        else:
            return None
            
    except Exception as e:
        logging.error(f"Error generating image for panel {panel.panel}: {str(e)}")
        return None

def create_comic_composite(panels: List[ComicPanel], title: str, aspect_ratio: str = "4:5"):
    """Create a composite image of all comic panels"""
    try:
        # Calculate dimensions based on aspect ratio
        if aspect_ratio == "4:5":
            width, height = 800, 1000
        elif aspect_ratio == "16:9":
            width, height = 1200, 675
        else:
            width, height = 800, 1000
        
        # Create blank canvas
        composite = Image.new('RGB', (width, height), color='#ffeaf5')
        draw = ImageDraw.Draw(composite)
        
        # Title area
        title_height = 100
        try:
            # Use default font if custom font fails
            font = ImageFont.load_default()
        except:
            font = None
        
        # Draw title
        if font:
            draw.text((width//2, 30), title, fill='#e74285', font=font, anchor='mt')
        
        # Calculate panel layout
        panels_per_row = 2 if len(panels) > 3 else 1
        panel_width = (width - 60) // panels_per_row
        panel_height = (height - title_height - 60) // ((len(panels) + panels_per_row - 1) // panels_per_row)
        
        # Place panels
        for i, panel in enumerate(panels):
            row = i // panels_per_row
            col = i % panels_per_row
            
            x = 30 + col * (panel_width + 20)
            y = title_height + 30 + row * (panel_height + 20)
            
            # Create panel background
            panel_bg = Image.new('RGB', (panel_width-20, panel_height-20), color='white')
            panel_draw = ImageDraw.Draw(panel_bg)
            
            # Draw panel border
            panel_draw.rectangle([0, 0, panel_width-21, panel_height-21], outline='#e74285', width=3)
            
            # Add panel image if available
            if panel.image_base64:
                try:
                    panel_image_data = base64.b64decode(panel.image_base64)
                    panel_image = Image.open(io.BytesIO(panel_image_data))
                    
                    # Resize to fit panel
                    panel_image = panel_image.resize((panel_width-40, panel_height-100))
                    panel_bg.paste(panel_image, (10, 10))
                except Exception as e:
                    logging.error(f"Error adding panel image: {e}")
            
            # Add panel number
            if font:
                panel_draw.text((15, panel_height-50), f"Panel {panel.panel}", fill='#1a1330', font=font)
            
            # Add dialogue if exists
            if panel.dialogue and font:
                # Simple text wrapping
                words = panel.dialogue.split()
                lines = []
                current_line = []
                for word in words:
                    if len(' '.join(current_line + [word])) < 30:
                        current_line.append(word)
                    else:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                if current_line:
                    lines.append(' '.join(current_line))
                
                for j, line in enumerate(lines[:3]):  # Max 3 lines
                    panel_draw.text((15, panel_height-40+j*15), line, fill='#1a1330', font=font)
            
            # Paste panel onto composite
            composite.paste(panel_bg, (x, y))
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        composite.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        return base64.b64encode(img_byte_arr).decode('utf-8')
        
    except Exception as e:
        logging.error(f"Error creating composite: {e}")
        return None

# Routes
@api_router.get("/")
async def root():
    return {"message": "Welcome to Mystical Whispers Comics API!"}

@api_router.post("/upload-character")
async def upload_character(name: str, file: UploadFile = File(...)):
    """Upload a character reference image"""
    try:
        # Read image
        contents = await file.read()
        
        # Convert to base64
        image_base64 = base64.b64encode(contents).decode('utf-8')
        
        # Analyze image for character description (simple version)
        description = f"Character reference for {name}"
        
        # Save character reference
        character = CharacterReference(
            name=name,
            description=description,
            image_base64=image_base64
        )
        
        await db.characters.insert_one(character.dict())
        
        return {"id": character.id, "name": name, "message": "Character uploaded successfully"}
        
    except Exception as e:
        logging.error(f"Error uploading character: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload character: {str(e)}")

@api_router.get("/characters")
async def get_characters():
    """Get all character references"""
    try:
        characters = await db.characters.find().to_list(100)
        return [CharacterReference(**char) for char in characters]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch characters")

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
            # Fallback
            panels = [
                ComicPanel(
                    panel=1,
                    scene="A mystical setting where the story unfolds",
                    dialogue=request.story[:200] + "..." if len(request.story) > 200 else request.story,
                    character_actions="Characters begin their journey",
                    mood="Mysterious and enchanting"
                )
            ]
        
        # Get character descriptions
        jamie_desc = "young adventurous girl with curious eyes"
        kylee_desc = "brave companion with wisdom beyond her years"
        
        characters = await db.characters.find().to_list(100)
        for char in characters:
            if char['name'].lower() == 'jamie':
                jamie_desc = char['description']
            elif char['name'].lower() == 'kylee':
                kylee_desc = char['description']
        
        # Generate images if requested
        if request.generate_images:
            for panel in panels:
                try:
                    image_base64 = await generate_panel_image(panel, request.style, jamie_desc, kylee_desc)
                    panel.image_base64 = image_base64
                except Exception as img_error:
                    logging.warning(f"Failed to generate image for panel {panel.panel}: {img_error}")
                    panel.image_base64 = None
        
        # Create storyboard response
        storyboard = StoryboardResponse(
            title=request.title or "Untitled Story",
            panels=panels,
            style=request.style,
            aspect_ratio=request.aspect_ratio
        )
        
        # Save to database
        comic_dict = Comic(
            title=storyboard.title,
            panels=storyboard.panels,
            story_text=request.story,
            style=request.style,
            aspect_ratio=request.aspect_ratio
        ).dict()
        
        await db.comics.insert_one(comic_dict)
        
        return storyboard
        
    except Exception as e:
        logging.error(f"Error parsing story: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to parse story: {str(e)}")

@api_router.get("/comics/{comic_id}/download")
async def download_comic_png(comic_id: str):
    """Download comic as PNG"""
    try:
        comic = await db.comics.find_one({"id": comic_id})
        if not comic:
            raise HTTPException(status_code=404, detail="Comic not found")
        
        comic_obj = Comic(**comic)
        
        # Create composite image
        composite_base64 = create_comic_composite(
            comic_obj.panels, 
            comic_obj.title, 
            comic_obj.aspect_ratio
        )
        
        if not composite_base64:
            raise HTTPException(status_code=500, detail="Failed to create comic image")
        
        # Convert base64 to bytes
        image_bytes = base64.b64decode(composite_base64)
        
        # Return as downloadable file
        return StreamingResponse(
            io.BytesIO(image_bytes),
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename={comic_obj.title.replace(' ', '_')}.png"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error downloading comic: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to download comic")

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
