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
import openai
import requests
import json
import base64
import io
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
import aiohttp

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

async def generate_placeholder_image(prompt: str, panel_number: int):
    """Generate a placeholder comic panel image for demonstration"""
    try:
        # Create a 512x512 placeholder image
        width, height = 512, 512
        image = Image.new('RGB', (width, height), color='#f0fff7')
        draw = ImageDraw.Draw(image)
        
        # Draw mystical gradient background
        for y in range(height):
            ratio = y / height
            r = int(255 - ratio * 30)
            g = int(240 + ratio * 15) 
            b = int(247 - ratio * 20)
            for x in range(width):
                image.putpixel((x, y), (r, g, b))
        
        draw = ImageDraw.Draw(image)
        
        # Draw mystical border
        border_color = '#e74285'
        for i in range(5):
            draw.rectangle([i, i, width-1-i, height-1-i], outline=border_color)
        
        # Draw panel number
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None
            
        if font:
            # Panel number badge
            badge_size = 40
            draw.ellipse([20, 20, 20 + badge_size, 20 + badge_size], fill='#e74285', outline='#1a1330', width=3)
            draw.text((20 + badge_size//2, 20 + badge_size//2), str(panel_number), fill='white', font=font, anchor='mm')
            
            # Add scene text
            scene_text = f"Panel {panel_number}: Mystical Scene"
            draw.text((width//2, height//2 - 40), scene_text, fill='#1a1330', font=font, anchor='mm')
            
            # Add prompt preview (truncated)
            prompt_preview = prompt[:50] + "..." if len(prompt) > 50 else prompt
            draw.text((width//2, height//2), prompt_preview, fill='#666', font=font, anchor='mm')
            
            # Add mystical elements
            draw.text((width//2, height//2 + 40), "✨ Mystical Comic Panel ✨", fill='#20b69e', font=font, anchor='mm')
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()
        
    except Exception as e:
        logging.error(f"Placeholder image generation failed: {e}")
        return None

async def generate_image_direct_openai(prompt: str):
    """Fallback image generation using direct OpenAI API"""
    try:
        client = openai.AsyncOpenAI(api_key=os.environ['EMERGENT_LLM_KEY'])
        
        response = await client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        # Download the image
        image_url = response.data[0].url
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status == 200:
                    image_bytes = await resp.read()
                    return image_bytes
                else:
                    logging.error(f"Failed to download image from {image_url}")
                    return None
                    
    except Exception as e:
        logging.error(f"Direct OpenAI image generation failed: {e}")
        return None

# Helper functions
def generate_stability_ai_image(panel: ComicPanel, style: str = "Mystical Watercolor"):
    """Generate an AI image using Stability AI for a comic panel"""
    try:
        api_key = os.getenv("STABILITY_API_KEY")
        if not api_key:
            logging.error("STABILITY_API_KEY not found")
            return None
            
        # Create detailed prompt using your exact format
        prompt = f"""
        {panel.scene}
        Include Jamie and Kylee in a {style} style.
        Mystical Whispers color palette:
        magenta #e74285, teal #20b69e, gold #fcd94c, navy #1a1330.
        Soft watercolor glow, cinematic tone.
        """
        
        # Use multipart/form-data but expect binary response
        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/generate/sd3",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "image/*"
            },
            files={
                "prompt": (None, prompt),
                "aspect_ratio": (None, "4:5"),
                "output_format": (None, "png")
            },
            timeout=60
        )
        
        if response.status_code == 200:
            # Convert raw binary image data to Base64
            image_bytes = response.content
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            logging.info(f"Successfully generated Stability AI image for panel {panel.panel}, size: {len(image_bytes)} bytes")
            return image_base64
        else:
            logging.error(f"Stability AI API error for panel {panel.panel}: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logging.error(f"Error generating Stability AI image for panel {panel.panel}: {str(e)}")
        return None

async def generate_panel_image(panel: ComicPanel, style: str = "Mystical Watercolor", jamie_desc: str = "", kylee_desc: str = ""):
    """Generate an AI image for a comic panel using Stability AI"""
    try:
        # Try Stability AI first
        image_base64 = generate_stability_ai_image(panel, style)
        if image_base64:
            return image_base64
            
        logging.warning(f"Stability AI failed for panel {panel.panel}, using placeholder")
        
        # Fallback to placeholder if Stability AI fails
        placeholder_bytes = await generate_placeholder_image(
            f"{panel.scene} - {style} style with mystical colors", 
            panel.panel
        )
        if placeholder_bytes:
            image_base64 = base64.b64encode(placeholder_bytes).decode('utf-8')
            return image_base64
            
        return None
            
    except Exception as e:
        logging.error(f"Error in panel image generation for panel {panel.panel}: {str(e)}")
        return None

def create_speech_bubble(draw, text, x, y, max_width=200, font=None):
    """Create a speech bubble with text"""
    if not font:
        font = ImageFont.load_default()
    
    # Wrap text
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] <= max_width and len(current_line) > 0:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    
    # Calculate bubble size
    line_height = 20
    padding = 15
    bubble_height = len(lines) * line_height + padding * 2
    
    # Draw bubble background (white with black border)
    bubble_rect = (x - padding, y - padding, x + max_width + padding, y + len(lines) * line_height + padding)
    draw.ellipse(bubble_rect, fill='white', outline='black', width=3)
    
    # Draw tail
    tail_points = [(x + max_width//2, y + bubble_height - padding), 
                   (x + max_width//2 - 15, y + bubble_height + 10),
                   (x + max_width//2 + 5, y + bubble_height - padding)]
    draw.polygon(tail_points, fill='white', outline='black')
    
    # Draw text
    for i, line in enumerate(lines):
        draw.text((x, y + i * line_height), line, fill='black', font=font)
    
    return bubble_height + 15

def create_comic_strip(panels: List[ComicPanel], title: str, aspect_ratio: str = "4:5"):
    """Create a professional comic strip with speech bubbles and proper layouts"""
    try:
        # Social media optimized dimensions
        if aspect_ratio == "4:5":  # Instagram post
            width, height = 1080, 1350
        elif aspect_ratio == "16:9":  # Twitter/landscape
            width, height = 1200, 675
        elif aspect_ratio == "9:16":  # Instagram story
            width, height = 1080, 1920
        else:
            width, height = 1080, 1350
        
        # Create main canvas with mystical gradient
        composite = Image.new('RGB', (width, height))
        
        # Create gradient background
        for y in range(height):
            ratio = y / height
            r = int(255 * (1 - ratio * 0.1))
            g = int(234 + ratio * 20)
            b = int(245 + ratio * 10)
            for x in range(width):
                composite.putpixel((x, y), (r, g, b))
        
        draw = ImageDraw.Draw(composite)
        
        # Load fonts
        try:
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default() 
        except Exception:
            title_font = None
            text_font = None
        
        # Title area
        title_height = 80
        if title_font:
            # Title background
            draw.rectangle([20, 10, width-20, title_height], fill='#e74285', outline='#1a1330', width=3)
            draw.text((width//2, title_height//2), title, fill='white', font=title_font, anchor='mm')
        
        # Calculate panel layout for vertical comic strip
        available_height = height - title_height - 40
        panel_height = available_height // len(panels)
        panel_width = width - 40
        
        # Create panels
        for i, panel in enumerate(panels):
            panel_y = title_height + 20 + i * panel_height
            
            # Panel border with mystical styling
            panel_rect = [20, panel_y, width-20, panel_y + panel_height - 10]
            draw.rectangle(panel_rect, fill='white', outline='#e74285', width=4)
            
            # Panel number badge
            badge_size = 30
            badge_x = 30
            badge_y = panel_y + 10
            draw.ellipse([badge_x, badge_y, badge_x + badge_size, badge_y + badge_size], 
                        fill='#e74285', outline='#1a1330', width=2)
            if text_font:
                draw.text((badge_x + badge_size//2, badge_y + badge_size//2), 
                         str(panel.panel), fill='white', font=text_font, anchor='mm')
            
            # Add AI generated panel image if available
            image_area_height = panel_height - 80  # Leave space for text
            if panel.image_base64:
                try:
                    panel_image_data = base64.b64decode(panel.image_base64)
                    panel_image = Image.open(io.BytesIO(panel_image_data))
                    
                    # Resize to fit panel while maintaining aspect ratio
                    img_width = panel_width - 60
                    img_height = image_area_height - 20
                    panel_image.thumbnail((img_width, img_height), Image.Resampling.LANCZOS)
                    
                    # Center the image
                    img_x = 40 + (img_width - panel_image.width) // 2
                    img_y = panel_y + 40
                    
                    composite.paste(panel_image, (img_x, img_y))
                    
                    # Add speech bubble if dialogue exists
                    if panel.dialogue and text_font:
                        bubble_x = img_x + 20
                        bubble_y = img_y + panel_image.height - 60
                        create_speech_bubble(draw, panel.dialogue, bubble_x, bubble_y, 
                                           min(300, panel_image.width - 40), text_font)
                
                except Exception as e:
                    logging.error(f"Error adding panel image: {e}")
                    # Fallback: just add text
                    if panel.dialogue and text_font:
                        draw.text((40, panel_y + 50), panel.dialogue, fill='#1a1330', font=text_font)
            else:
                # No image: create text-based panel
                if panel.scene and text_font:
                    scene_text = f"Scene: {panel.scene}"
                    draw.text((40, panel_y + 40), scene_text[:100] + "...", fill='#1a1330', font=text_font)
                
                if panel.dialogue and text_font:
                    bubble_x = 40
                    bubble_y = panel_y + 80
                    create_speech_bubble(draw, panel.dialogue, bubble_x, bubble_y, 
                                       panel_width - 100, text_font)
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        composite.save(img_byte_arr, format='PNG', quality=95)
        img_byte_arr = img_byte_arr.getvalue()
        
        return base64.b64encode(img_byte_arr).decode('utf-8')
        
    except Exception as e:
        logging.error(f"Error creating comic strip: {e}")
        return None

def create_comic_composite(panels: List[ComicPanel], title: str, aspect_ratio: str = "4:5"):
    """Create a composite comic strip - now uses the enhanced comic strip generator"""
    return create_comic_strip(panels, title, aspect_ratio)

# Routes
@api_router.get("/")
async def root():
    return {"message": "Welcome to Mystical Whispers Comics API!"}

@api_router.get("/test-image")
async def test_image_generation():
    """Test endpoint for image generation"""
    # Create a test panel
    test_panel = ComicPanel(
        panel=1,
        scene="A magical crystal glowing in an enchanted forest with Jamie and Kylee standing nearby in wonder",
        dialogue="Look at that beautiful crystal!",
        character_actions="Jamie points excitedly while Kylee stares in amazement",
        mood="Mystical and wondrous"
    )
    
    # Test Stability AI
    try:
        image_base64 = generate_stability_ai_image(test_panel, "Mystical Watercolor")
        if image_base64:
            return {"success": True, "method": "stability_ai", "image_size": len(image_base64), "has_image": True}
        else:
            return {"success": False, "error": "Stability AI returned no image"}
    except Exception as e:
        return {"success": False, "error": f"Stability AI test failed: {str(e)}"}

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
    except Exception:
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
