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
from io import BytesIO

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
        Every panel must reflect the Mystical Whispers world — sacred rituals, tarot spreads, candles, constellations, ancestral energy, feathers, the Codex, and the Love Ledger.
        Themes: transformation, embodiment, intuition, divine feminine power.
        Never write violent, erotic, or sci-fi scenes.
        
        Parse stories into 5-8 mystical comic panels focusing on:
        - Tarot card readings and spiritual guidance
        - Candlelit meditation and ritual spaces  
        - Astrology charts and celestial wisdom
        - Sacred feminine energy and sisterhood
        - Ancestral connections and ancient wisdom
        - Crystal healing and energy work
        - Moon phases and celestial events
        - Sacred geometry and mystical symbols
        
        Each panel should have:
        - Panel number
        - Scene description (mystical, sacred settings with Jamie and Kylee)
        - Character actions (spiritual practices, sisterhood moments)
        - Dialogue (wisdom, affirmations, mystical insights)
        - Mood (sacred, peaceful, transformative)
        
        Always include mystical elements: candles, crystals, tarot cards, feathers, gold ink, sacred texts, moon imagery.
        
        IMPORTANT: Return ONLY a valid JSON array with no additional text. Format exactly like this:
        [{
          "panel": 1,
          "scene": "Jamie and Kylee sit at a candlelit table with tarot cards spread between them, moonlight streaming through crystal-adorned windows, feathers and gold ink nearby, sacred geometry patterns glowing softly on the walls",
          "dialogue": "The cards are calling to us, sister. What wisdom do they hold?",
          "character_actions": "Jamie gently touches a tarot card while Kylee lights a white candle with reverent focus",
          "mood": "Sacred and mystical"
        }]
        
        Make scene descriptions rich and detailed for AI image generation. Do not include any explanations, markdown formatting, or extra text."""
    ).with_model("openai", "gpt-4o-mini")

# Initialize Image Generation
def get_image_generator():
    return OpenAIImageGeneration(api_key=os.environ['EMERGENT_LLM_KEY'])

async def generate_enhanced_comic_placeholder(prompt: str, panel_number: int, style: str = "Mystical Watercolor"):
    """Generate an enhanced comic-style placeholder that looks like a real comic panel"""
    try:
        # Create a high-res image for comic quality
        width, height = 800, 1000  # 4:5 aspect ratio
        image = Image.new('RGB', (width, height), color='#f8f9fa')
        draw = ImageDraw.Draw(image)
        
        # Create mystical gradient background
        for y in range(height):
            ratio = y / height
            # Mystical gradient from light pink to light teal
            r = int(255 - ratio * 15)  # Light pink to white
            g = int(245 + ratio * 10)  # Maintain high values
            b = int(250 - ratio * 5)   # Very light variation
            
            for x in range(width):
                # Add slight horizontal variation for mystical effect
                x_ratio = x / width
                r_final = max(220, r - int(x_ratio * 10))
                g_final = max(230, g - int(x_ratio * 5))
                b_final = max(240, b - int(x_ratio * 5))
                image.putpixel((x, y), (r_final, g_final, b_final))
        
        draw = ImageDraw.Draw(image)
        
        # Draw comic panel border
        border_color = '#e74285'
        border_width = 6
        for i in range(border_width):
            draw.rectangle([i, i, width-1-i, height-1-i], outline=border_color)
        
        # Draw mystical elements
        # Add floating crystals/gems
        gem_color = '#20b69e'
        for i in range(8):
            gem_x = 100 + (i * 80)
            gem_y = 50 + (i % 3) * 30
            if gem_x < width - 50:
                draw.ellipse([gem_x, gem_y, gem_x + 20, gem_y + 20], fill=gem_color, outline='#1a1330', width=2)
        
        # Add mystical stars
        star_color = '#fcd94c'
        for i in range(15):
            star_x = (i * 47) % (width - 40) + 20
            star_y = (i * 73) % (height - 40) + 20
            draw.ellipse([star_x, star_y, star_x + 6, star_y + 6], fill=star_color, outline='#1a1330')
        
        # Draw central mystical scene area
        scene_area = [50, 100, width-50, height-200]
        draw.rectangle(scene_area, fill='#ffffff', outline='#20b69e', width=3)
        
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None
            
        if font:
            # Panel number badge (larger and more prominent)
            badge_size = 60
            badge_x = width - badge_size - 20
            badge_y = 20
            draw.ellipse([badge_x, badge_y, badge_x + badge_size, badge_y + badge_size], 
                        fill='#e74285', outline='#1a1330', width=4)
            draw.text((badge_x + badge_size//2, badge_y + badge_size//2), 
                     str(panel_number), fill='white', font=font, anchor='mm')
            
            # Add "MYSTICAL COMIC PANEL" title
            title_y = scene_area[1] + 20
            draw.text((width//2, title_y), f"✨ {style} Comic Panel ✨", 
                     fill='#1a1330', font=font, anchor='mm')
            
            # Add scene description (word wrapped)
            scene_lines = []
            words = prompt.replace('\n', ' ').split()
            current_line = []
            chars_per_line = 35
            
            for word in words:
                if len(' '.join(current_line + [word])) <= chars_per_line:
                    current_line.append(word)
                else:
                    if current_line:
                        scene_lines.append(' '.join(current_line))
                    current_line = [word]
            if current_line:
                scene_lines.append(' '.join(current_line))
            
            # Draw scene text (max 6 lines)
            text_y = title_y + 40
            for i, line in enumerate(scene_lines[:6]):
                draw.text((width//2, text_y + i * 20), line, fill='#333', font=font, anchor='mm')
            
            # Add Jamie and Kylee character placeholders
            char_y = height - 150
            draw.text((width//4, char_y), "👧 Jamie", fill='#e74285', font=font, anchor='mm')
            draw.text((3*width//4, char_y), "👧 Kylee", fill='#20b69e', font=font, anchor='mm')
            
            # Add mystical footer
            footer_text = "🔮 Awaiting Stability AI Credits for Real Artwork 🔮"
            draw.text((width//2, height - 40), footer_text, fill='#666', font=font, anchor='mm')
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()
        
    except Exception as e:
        logging.error(f"Enhanced placeholder generation failed: {e}")
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
async def get_character_images():
    """Retrieve character images for reference"""
    try:
        characters = db.characters.find().to_list(length=None)
        jamie_image = None
        kylee_image = None
        
        for char in await characters:
            if char['name'].lower() == 'jamie' and char.get('image_base64'):
                jamie_image = char['image_base64']
            elif char['name'].lower() == 'kylee' and char.get('image_base64'):
                kylee_image = char['image_base64']
        
        return jamie_image, kylee_image
    except Exception as e:
        logging.error(f"Error retrieving character images: {e}")
        return None, None

def generate_stability_ai_image(panel: ComicPanel, style: str = "Mystical Watercolor", jamie_desc: str = "", kylee_desc: str = ""):
    """Generate an AI image using Stability AI DreamShaper XL with character references"""
    try:
        api_key = os.getenv("STABILITY_API_KEY")
        if not api_key:
            logging.error("STABILITY_API_KEY not found")
            return None
        
        # Traditional comic book prompt with character references
        prompt = f"""
        A comic panel of Jamie and Kylee in the Mystical Whispers universe.
        Scene: {panel.scene}
        Style: traditional comic strip with watercolor ink texture and hand-drawn outlines.
        Mood: mystical, soulful, and cinematic — tarot cards, candles, feathers, moonlight, stars, books, sacred symbols, not religious.
        Setting: warm candlelight, celestial patterns, gentle magic.
        Characters: Jamie and Kylee — real women, grounded, creative, and powerful.
        Jamie: long dark hair, confident, tech-mystic energy.
        Kylee: blonde hair, radiant, oceanic and intuitive.
        Avoid religious imagery, crosses, angels, churches, or saints.
        Use the Mystical Whispers color palette: magenta #e74285, teal #20b69e, gold #fcd94c, navy #1a1330.
        """
        
        negative_prompt = """
        nsfw, naked, sexy, cleavage, church, priest, halo, saint, Jesus, cross, bible, crucifix, old testament, religious art, biblical, monk, nun, demon, satanic, horror, ugly hands, distorted faces, mandala, abstract patterns, geometric shapes only, no characters, blur, low quality
        """
        
        # Try DreamShaper XL v2beta API first
        try:
            response = requests.post(
                "https://api.stability.ai/v2beta/stable-image/generate/dreamshaper-xl",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Accept": "image/*"
                },
                files={
                    "prompt": (None, prompt),
                    "negative_prompt": (None, negative_prompt),
                    "aspect_ratio": (None, "3:4"),
                    "seed": (None, "0"),
                    "output_format": (None, "png")
                },
                timeout=120
            )
            
            if response.status_code == 200:
                # Convert binary image to base64
                image_base64 = base64.b64encode(response.content).decode('utf-8')
                logging.info(f"Successfully generated DreamShaper XL image for panel {panel.panel}, base64 length: {len(image_base64)}")
                return image_base64
            else:
                logging.warning(f"DreamShaper XL failed: {response.status_code}, falling back to SDXL")
        
        except Exception as e:
            logging.warning(f"DreamShaper XL error: {e}, falling back to SDXL")
        
        # Fallback to SDXL v1 API
        response = requests.post(
            "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            json={
                "text_prompts": [
                    {"text": prompt, "weight": 1.0},
                    {"text": negative_prompt, "weight": -1.0}
                ],
                "cfg_scale": 12,
                "height": 1024,
                "width": 768,  # 3:4 aspect ratio for comic panels
                "steps": 30,
                "samples": 1,
                "sampler": "K_DPM_2_ANCESTRAL"
            },
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            # V1 API response format
            if "artifacts" in data and len(data["artifacts"]) > 0:
                image_base64 = data["artifacts"][0]["base64"]
                logging.info(f"Successfully generated Stability AI image for panel {panel.panel} using v1 API, base64 length: {len(image_base64)}")
                return image_base64
            else:
                logging.error(f"No artifacts in Stability AI v1 response for panel {panel.panel}: {data}")
                return None
        else:
            logging.error(f"Stability AI v1 API error for panel {panel.panel}: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logging.error(f"Error generating Stability AI image for panel {panel.panel}: {str(e)}")
        return None

def compress_image_for_storage(image_base64: str, max_size_mb: float = 1.5) -> str:
    """Compress base64 image for MongoDB storage while maintaining quality"""
    try:
        # Decode base64 to bytes
        image_bytes = base64.b64decode(image_base64)
        
        # Load image with PIL
        image = Image.open(BytesIO(image_bytes))
        
        # Start with high quality and reduce if needed
        quality = 90  # Start higher for better quality
        max_size_bytes = max_size_mb * 1024 * 1024
        
        while quality > 30:  # Don't go too low on quality
            # Convert to bytes with current quality
            output_buffer = BytesIO()
            image.save(output_buffer, format='JPEG', quality=quality, optimize=True)
            compressed_bytes = output_buffer.getvalue()
            
            # Check if size is acceptable
            if len(compressed_bytes) <= max_size_bytes:
                compressed_base64 = base64.b64encode(compressed_bytes).decode('utf-8')
                logging.info(f"Compressed image from {len(image_bytes)} to {len(compressed_bytes)} bytes at quality {quality}")
                return compressed_base64
            
            quality -= 5  # Smaller quality reduction steps
        
        # If still too large, resize image and try again
        logging.warning("Image still too large after quality compression, resizing...")
        original_size = image.size
        new_size = (int(original_size[0] * 0.8), int(original_size[1] * 0.8))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        output_buffer = BytesIO()
        image.save(output_buffer, format='JPEG', quality=70, optimize=True)
        compressed_bytes = output_buffer.getvalue()
        compressed_base64 = base64.b64encode(compressed_bytes).decode('utf-8')
        
        logging.info(f"Final compressed image: {len(compressed_bytes)} bytes after resize from {original_size} to {new_size}")
        return compressed_base64
        
    except Exception as e:
        logging.error(f"Error compressing image: {e}")
        return image_base64  # Return original if compression fails

async def generate_panel_image(panel: ComicPanel, style: str = "Mystical Watercolor", jamie_desc: str = "", kylee_desc: str = ""):
    """Generate an AI image for a comic panel using Stability AI"""
    try:
        # Try Stability AI first with character descriptions
        image_base64 = generate_stability_ai_image(panel, style, jamie_desc, kylee_desc)
        if image_base64:
            # Compress the image for storage to avoid MongoDB document size limits
            compressed_image = compress_image_for_storage(image_base64, max_size_mb=1.5)
            return compressed_image
            
        logging.warning(f"Stability AI failed for panel {panel.panel}, using placeholder")
        
        # Fallback to enhanced placeholder if Stability AI fails
        placeholder_bytes = await generate_enhanced_comic_placeholder(
            f"{panel.scene} - {style} style with mystical colors", 
            panel.panel,
            style
        )
        if placeholder_bytes:
            image_base64 = base64.b64encode(placeholder_bytes).decode('utf-8')
            # Compress placeholder too
            compressed_image = compress_image_for_storage(image_base64, max_size_mb=1.0)
            return compressed_image
            
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
    
    # Test complete pipeline
    try:
        # First test Stability AI directly with enhanced character descriptions
        jamie_test_desc = "spiritual guide with beautiful facial features, wearing modest mystical robes, hands holding crystals"
        kylee_test_desc = "gentle mystical companion with soft features, flowing hair, surrounded by spiritual light"
        stability_result = generate_stability_ai_image(test_panel, "Mystical Watercolor", jamie_test_desc, kylee_test_desc)
        if stability_result:
            return {
                "success": True, 
                "method": "stability_ai", 
                "image_size": len(stability_result), 
                "has_image": True, 
                "note": "Successfully generated real AI image using Stability AI"
            }
        
        # Fall back to complete pipeline if direct fails
        image_base64 = await generate_panel_image(test_panel, "Mystical Watercolor")
        if image_base64:
            # Check if it's a real AI image or placeholder by size
            if len(image_base64) > 1000000:  # Real images are typically larger
                method = "stability_ai_via_pipeline"
                note = "Successfully generated real AI image via pipeline"
            else:
                method = "enhanced_placeholder"
                note = "Using enhanced placeholder - Stability AI may have failed"
            
            return {
                "success": True, 
                "method": method, 
                "image_size": len(image_base64), 
                "has_image": True, 
                "note": note
            }
        else:
            return {"success": False, "error": "Image generation pipeline failed completely"}
    except Exception as e:
        return {"success": False, "error": f"Image generation test failed: {str(e)}"}

@api_router.post("/upload-character")
async def upload_character(name: str, file: UploadFile = File(...)):
    """Upload a character reference image"""
    try:
        # Read image
        contents = await file.read()
        
        # Convert to base64
        image_base64 = base64.b64encode(contents).decode('utf-8')
        
        # Create enhanced character description based on name and uploaded image - focused on face and spiritual energy
        if name.lower() == 'jamie':
            description = "Jamie: Spiritual guide with beautiful facial features, expressive eyes full of wisdom, elegant flowing hair, wearing modest mystical robes or flowing dresses, serene and confident expression, hands often holding crystals or tarot cards"
        elif name.lower() == 'kylee':
            description = "Kylee: Gentle mystical companion with soft facial features, flowing hair with ethereal quality, wearing elegant modest clothing, kind and intuitive expression, surrounded by soft spiritual light and sacred energy"
        else:
            description = f"Character reference for {name}: Mystical spiritual person with sacred energy and modest elegant appearance"
        
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
