#!/usr/bin/env python3
"""
Quick test to verify image dimensions after fix
"""

import requests
import json
import base64
from PIL import Image
from io import BytesIO

BACKEND_URL = "https://wealth-comics.preview.emergentagent.com/api"

def test_image_dimensions():
    """Test that images now have correct 896x1152 dimensions"""
    try:
        print("Testing corrected image dimensions...")
        
        test_story = {
            "story": "Jamie examines a glowing crystal while Kylee reads from an ancient mystical tome.",
            "title": "Dimension Fix Test",
            "style": "Mystical Watercolor",
            "aspect_ratio": "4:5",
            "generate_images": True
        }
        
        response = requests.post(
            f"{BACKEND_URL}/parse-story", 
            json=test_story, 
            timeout=120,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            panels = data.get("panels", [])
            
            print(f"Generated {len(panels)} panels")
            
            for i, panel in enumerate(panels):
                if panel.get("image_base64"):
                    try:
                        image_data = base64.b64decode(panel["image_base64"])
                        image = Image.open(BytesIO(image_data))
                        width, height = image.size
                        
                        print(f"Panel {i+1}: {width}x{height}")
                        
                        if width == 896 and height == 1152:
                            print(f"  ✅ Correct dimensions (896x1152 landscape)")
                        else:
                            print(f"  ❌ Incorrect dimensions (expected 896x1152)")
                            
                    except Exception as e:
                        print(f"Panel {i+1}: Error decoding image - {e}")
                else:
                    print(f"Panel {i+1}: No image data")
        else:
            print(f"Request failed: {response.status_code}")
            
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_image_dimensions()