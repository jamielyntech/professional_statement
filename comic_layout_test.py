#!/usr/bin/env python3
"""
Comic Layout System Backend Testing
Focus: Enhanced comic book layout system with 896x1152 landscape format and speech bubble support
"""

import requests
import json
import base64
import time
import os
from datetime import datetime
from PIL import Image
from io import BytesIO

# Configuration
BACKEND_URL = "https://wealth-comics.preview.emergentagent.com/api"
TEST_TIMEOUT = 120

def log_test(test_name, status, details=""):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"[{timestamp}] {status_symbol} {test_name}: {status}")
    if details:
        print(f"    Details: {details}")
    print()

def test_image_dimensions_896x1152():
    """Test that generated images have correct 896x1152 landscape dimensions"""
    try:
        print("Testing image dimensions (896x1152 landscape format)...")
        response = requests.get(f"{BACKEND_URL}/test-image", timeout=TEST_TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success") and data.get("image_size", 0) > 500000:
                # For this test, we need to generate a comic to get actual image data
                test_story = {
                    "story": "Jamie examines ancient mystical symbols while Kylee lights ceremonial candles in their sacred study room.",
                    "title": "Image Dimension Test Comic",
                    "style": "Mystical Watercolor",
                    "aspect_ratio": "4:5",
                    "generate_images": True
                }
                
                comic_response = requests.post(
                    f"{BACKEND_URL}/parse-story", 
                    json=test_story, 
                    timeout=TEST_TIMEOUT,
                    headers={"Content-Type": "application/json"}
                )
                
                if comic_response.status_code == 200:
                    comic_data = comic_response.json()
                    panels = comic_data.get("panels", [])
                    
                    dimension_checks = []
                    for i, panel in enumerate(panels):
                        if panel.get("image_base64"):
                            try:
                                # Decode and check image dimensions
                                image_data = base64.b64decode(panel["image_base64"])
                                image = Image.open(BytesIO(image_data))
                                width, height = image.size
                                
                                # Check if dimensions match expected 896x1152 (landscape)
                                if width == 896 and height == 1152:
                                    dimension_checks.append(f"Panel {i+1}: ✅ {width}x{height} (correct)")
                                elif width == 1152 and height == 896:
                                    dimension_checks.append(f"Panel {i+1}: ⚠️ {width}x{height} (portrait instead of landscape)")
                                else:
                                    dimension_checks.append(f"Panel {i+1}: ❌ {width}x{height} (incorrect dimensions)")
                                    
                            except Exception as e:
                                dimension_checks.append(f"Panel {i+1}: ❌ Could not decode image: {str(e)}")
                    
                    if dimension_checks:
                        correct_dimensions = sum(1 for check in dimension_checks if "✅" in check)
                        total_panels = len(dimension_checks)
                        
                        details = f"Dimension check results:\n" + "\n".join([f"    {check}" for check in dimension_checks])
                        
                        if correct_dimensions == total_panels:
                            log_test("Image Dimensions (896x1152)", "PASS", details)
                            return True
                        elif correct_dimensions > 0:
                            log_test("Image Dimensions (896x1152)", "WARNING", details)
                            return False
                        else:
                            log_test("Image Dimensions (896x1152)", "FAIL", details)
                            return False
                    else:
                        log_test("Image Dimensions (896x1152)", "FAIL", "No images found to check dimensions")
                        return False
                else:
                    log_test("Image Dimensions (896x1152)", "FAIL", f"Comic generation failed: {comic_response.status_code}")
                    return False
            else:
                log_test("Image Dimensions (896x1152)", "FAIL", "Image generation not working")
                return False
        else:
            log_test("Image Dimensions (896x1152)", "FAIL", f"Test image endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Image Dimensions (896x1152)", "FAIL", f"Exception: {str(e)}")
        return False

def test_speech_bubble_data_structure():
    """Test that comic panels contain proper dialogue data for speech bubble overlays"""
    try:
        print("Testing speech bubble data structure...")
        
        test_story = {
            "story": "Jamie points to mystical symbols in an ancient book and says 'Look at these patterns, Kylee!' Kylee responds 'They seem to glow with inner light!' as she examines the magical text.",
            "title": "Speech Bubble Test Comic",
            "style": "Mystical Watercolor",
            "aspect_ratio": "4:5",
            "generate_images": True
        }
        
        response = requests.post(
            f"{BACKEND_URL}/parse-story", 
            json=test_story, 
            timeout=TEST_TIMEOUT,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            panels = data.get("panels", [])
            
            dialogue_checks = []
            action_checks = []
            
            for i, panel in enumerate(panels):
                panel_num = panel.get("panel", i+1)
                dialogue = panel.get("dialogue", "")
                character_actions = panel.get("character_actions", "")
                scene = panel.get("scene", "")
                
                # Check dialogue content
                if dialogue and len(dialogue.strip()) > 0:
                    dialogue_checks.append(f"Panel {panel_num}: ✅ Has dialogue: '{dialogue[:50]}...'")
                else:
                    dialogue_checks.append(f"Panel {panel_num}: ❌ No dialogue")
                
                # Check character actions for overlay positioning
                if character_actions and len(character_actions.strip()) > 0:
                    action_checks.append(f"Panel {panel_num}: ✅ Has actions: '{character_actions[:50]}...'")
                else:
                    action_checks.append(f"Panel {panel_num}: ❌ No character actions")
            
            panels_with_dialogue = sum(1 for check in dialogue_checks if "✅" in check)
            panels_with_actions = sum(1 for check in action_checks if "✅" in check)
            total_panels = len(panels)
            
            details = "Dialogue checks:\n" + "\n".join([f"    {check}" for check in dialogue_checks])
            details += "\nAction checks:\n" + "\n".join([f"    {check}" for check in action_checks])
            
            if panels_with_dialogue >= total_panels * 0.8:  # 80% should have dialogue
                log_test("Speech Bubble Data Structure", "PASS", 
                       f"{panels_with_dialogue}/{total_panels} panels have dialogue, {panels_with_actions}/{total_panels} have actions\n{details}")
                return True
            else:
                log_test("Speech Bubble Data Structure", "FAIL", 
                       f"Only {panels_with_dialogue}/{total_panels} panels have dialogue\n{details}")
                return False
        else:
            log_test("Speech Bubble Data Structure", "FAIL", f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Speech Bubble Data Structure", "FAIL", f"Exception: {str(e)}")
        return False

def test_saved_comics_count():
    """Test that saved comics are properly stored and retrievable"""
    try:
        print("Testing saved comics storage and retrieval...")
        
        response = requests.get(f"{BACKEND_URL}/comics", timeout=30)
        
        if response.status_code == 200:
            comics = response.json()
            
            if isinstance(comics, list):
                comics_count = len(comics)
                
                # Check if we have comics with proper structure
                valid_comics = 0
                comics_with_images = 0
                
                for comic in comics:
                    if all(key in comic for key in ["id", "title", "panels"]):
                        valid_comics += 1
                        
                        # Check if comic has images
                        panels = comic.get("panels", [])
                        panels_with_images = sum(1 for panel in panels if panel.get("image_base64"))
                        if panels_with_images > 0:
                            comics_with_images += 1
                
                details = f"Total comics: {comics_count}, Valid structure: {valid_comics}, With images: {comics_with_images}"
                
                if comics_count > 0 and valid_comics == comics_count:
                    log_test("Saved Comics Count", "PASS", details)
                    return True, comics_count
                elif comics_count > 0:
                    log_test("Saved Comics Count", "WARNING", f"Some comics have invalid structure. {details}")
                    return False, comics_count
                else:
                    log_test("Saved Comics Count", "FAIL", "No saved comics found")
                    return False, 0
            else:
                log_test("Saved Comics Count", "FAIL", "Response is not a list")
                return False, 0
        else:
            log_test("Saved Comics Count", "FAIL", f"HTTP {response.status_code}")
            return False, 0
            
    except Exception as e:
        log_test("Saved Comics Count", "FAIL", f"Exception: {str(e)}")
        return False, 0

def test_comic_panel_layout_structure():
    """Test that comic panels have proper structure for fixed height containers"""
    try:
        print("Testing comic panel layout structure...")
        
        # Generate a test comic with multiple panels
        test_story = {
            "story": "Jamie and Kylee discover a mystical library. Panel 1: They enter through glowing doors. Panel 2: Jamie reads from an ancient tome while Kylee examines crystal orbs. Panel 3: Magical energy swirls around them as they unlock ancient secrets. Panel 4: They emerge transformed with new mystical knowledge.",
            "title": "Panel Layout Test Comic",
            "style": "Mystical Watercolor",
            "aspect_ratio": "4:5",
            "generate_images": True
        }
        
        response = requests.post(
            f"{BACKEND_URL}/parse-story", 
            json=test_story, 
            timeout=TEST_TIMEOUT,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            panels = data.get("panels", [])
            
            if len(panels) >= 3:  # Should have multiple panels for layout testing
                structure_checks = []
                
                for i, panel in enumerate(panels):
                    panel_num = panel.get("panel", i+1)
                    required_fields = ["panel", "scene", "dialogue"]
                    optional_fields = ["character_actions", "mood", "image_base64"]
                    
                    missing_required = [field for field in required_fields if not panel.get(field)]
                    present_optional = [field for field in optional_fields if panel.get(field)]
                    
                    if not missing_required:
                        structure_checks.append(f"Panel {panel_num}: ✅ Complete structure ({len(present_optional)} optional fields)")
                    else:
                        structure_checks.append(f"Panel {panel_num}: ❌ Missing: {missing_required}")
                
                complete_panels = sum(1 for check in structure_checks if "✅" in check)
                total_panels = len(panels)
                
                details = f"Panel structure checks:\n" + "\n".join([f"    {check}" for check in structure_checks])
                details += f"\nTotal panels: {total_panels}, Complete: {complete_panels}"
                
                if complete_panels == total_panels:
                    log_test("Comic Panel Layout Structure", "PASS", details)
                    return True
                else:
                    log_test("Comic Panel Layout Structure", "FAIL", details)
                    return False
            else:
                log_test("Comic Panel Layout Structure", "FAIL", f"Only {len(panels)} panels generated, need at least 3 for layout testing")
                return False
        else:
            log_test("Comic Panel Layout Structure", "FAIL", f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Comic Panel Layout Structure", "FAIL", f"Exception: {str(e)}")
        return False

def test_image_compression_for_400px_containers():
    """Test that images are properly compressed for 400px height containers"""
    try:
        print("Testing image compression for 400px containers...")
        
        # Generate a comic and check image sizes
        test_story = {
            "story": "Jamie holds a glowing crystal while Kylee examines mystical charts in their candlelit study.",
            "title": "Image Compression Test",
            "style": "Mystical Watercolor", 
            "aspect_ratio": "4:5",
            "generate_images": True
        }
        
        response = requests.post(
            f"{BACKEND_URL}/parse-story",
            json=test_story,
            timeout=TEST_TIMEOUT,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            panels = data.get("panels", [])
            
            compression_checks = []
            
            for i, panel in enumerate(panels):
                if panel.get("image_base64"):
                    try:
                        image_data = base64.b64decode(panel["image_base64"])
                        image = Image.open(BytesIO(image_data))
                        width, height = image.size
                        file_size = len(image_data)
                        
                        # Check if image is appropriately sized for web display
                        # Images should be compressed but still high quality
                        if file_size < 2000000:  # Less than 2MB (good for web)
                            if file_size > 100000:  # But still substantial (not over-compressed)
                                compression_checks.append(f"Panel {i+1}: ✅ {file_size:,} bytes ({width}x{height}) - Good compression")
                            else:
                                compression_checks.append(f"Panel {i+1}: ⚠️ {file_size:,} bytes ({width}x{height}) - May be over-compressed")
                        else:
                            compression_checks.append(f"Panel {i+1}: ❌ {file_size:,} bytes ({width}x{height}) - Too large for web")
                            
                    except Exception as e:
                        compression_checks.append(f"Panel {i+1}: ❌ Could not analyze image: {str(e)}")
                else:
                    compression_checks.append(f"Panel {i+1}: ❌ No image data")
            
            if compression_checks:
                good_compression = sum(1 for check in compression_checks if "✅" in check)
                total_images = len(compression_checks)
                
                details = "Compression analysis:\n" + "\n".join([f"    {check}" for check in compression_checks])
                
                if good_compression >= total_images * 0.8:  # 80% should be well compressed
                    log_test("Image Compression for 400px Containers", "PASS", details)
                    return True
                else:
                    log_test("Image Compression for 400px Containers", "WARNING", details)
                    return False
            else:
                log_test("Image Compression for 400px Containers", "FAIL", "No images to analyze")
                return False
        else:
            log_test("Image Compression for 400px Containers", "FAIL", f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Image Compression for 400px Containers", "FAIL", f"Exception: {str(e)}")
        return False

def main():
    """Run comic layout system backend tests"""
    print("=" * 80)
    print("COMIC LAYOUT SYSTEM - BACKEND TESTING")
    print("Focus: Enhanced comic book layout with 896x1152 format and speech bubbles")
    print("=" * 80)
    print()
    
    results = {}
    
    # Test 1: Image Dimensions (896x1152 landscape)
    results['image_dimensions'] = test_image_dimensions_896x1152()
    
    # Test 2: Speech Bubble Data Structure
    results['speech_bubble_data'] = test_speech_bubble_data_structure()
    
    # Test 3: Saved Comics Count
    results['saved_comics'], comics_count = test_saved_comics_count()
    
    # Test 4: Comic Panel Layout Structure
    results['panel_layout'] = test_comic_panel_layout_structure()
    
    # Test 5: Image Compression for 400px Containers
    results['image_compression'] = test_image_compression_for_400px_containers()
    
    # Summary
    print("=" * 80)
    print("COMIC LAYOUT SYSTEM TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    print()
    
    # Individual test results
    test_names = {
        'image_dimensions': 'Image Dimensions (896x1152)',
        'speech_bubble_data': 'Speech Bubble Data Structure', 
        'saved_comics': 'Saved Comics Storage',
        'panel_layout': 'Comic Panel Layout Structure',
        'image_compression': 'Image Compression for 400px Containers'
    }
    
    print("DETAILED RESULTS:")
    for test_key, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        test_name = test_names.get(test_key, test_key)
        print(f"  {status} {test_name}")
    
    print()
    
    if comics_count > 0:
        print(f"📚 Found {comics_count} saved comics in database")
    
    if passed == total:
        print("\n🎉 ALL COMIC LAYOUT TESTS PASSED!")
        print("✅ Images have correct 896x1152 landscape dimensions")
        print("✅ Speech bubble data structure is complete")
        print("✅ Comics are properly saved and retrievable")
        print("✅ Panel layout structure supports fixed height containers")
        print("✅ Images are properly compressed for web display")
    elif passed >= total * 0.8:
        print(f"\n⚠️ MOSTLY SUCCESSFUL - {passed}/{total} tests passed")
        print("Comic layout system is mostly working with some issues")
    else:
        print(f"\n❌ SIGNIFICANT ISSUES - Only {passed}/{total} tests passed")
        print("Comic layout system needs attention")
    
    return results

if __name__ == "__main__":
    main()