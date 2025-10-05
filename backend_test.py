#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Mystical Whispers Comics
Focus: Real AI Image Generation and Comic Pipeline Testing
"""

import requests
import json
import base64
import time
import os
from datetime import datetime

# Configuration
BACKEND_URL = "https://whisper-comics.preview.emergentagent.com/api"
TEST_TIMEOUT = 60

def log_test(test_name, status, details=""):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"[{timestamp}] {status_symbol} {test_name}: {status}")
    if details:
        print(f"    Details: {details}")
    print()

def test_api_health():
    """Test basic API connectivity"""
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "Welcome to Mystical Whispers Comics API" in data.get("message", ""):
                log_test("API Health Check", "PASS", f"API responding correctly: {data['message']}")
                return True
            else:
                log_test("API Health Check", "FAIL", f"Unexpected response: {data}")
                return False
        else:
            log_test("API Health Check", "FAIL", f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test("API Health Check", "FAIL", f"Connection error: {str(e)}")
        return False

def test_stability_ai_integration():
    """Test the /api/test-image endpoint for real AI image generation"""
    try:
        print("Testing Stability AI integration - this may take 30-60 seconds...")
        response = requests.get(f"{BACKEND_URL}/test-image", timeout=TEST_TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if the test was successful
            if data.get("success"):
                method = data.get("method", "unknown")
                image_size = data.get("image_size", 0)
                note = data.get("note", "")
                
                # Real AI images should be large (typically 1MB+ after base64 encoding)
                if image_size > 1000000:  # 1MB threshold for real images
                    log_test("Stability AI Integration", "PASS", 
                           f"Method: {method}, Image size: {image_size:,} bytes, Note: {note}")
                    return True, "real_ai"
                elif image_size > 100000:  # Smaller but still substantial
                    log_test("Stability AI Integration", "WARNING", 
                           f"Method: {method}, Image size: {image_size:,} bytes (smaller than expected), Note: {note}")
                    return True, "compressed_ai"
                else:
                    log_test("Stability AI Integration", "FAIL", 
                           f"Method: {method}, Image size: {image_size:,} bytes (likely placeholder), Note: {note}")
                    return False, "placeholder"
            else:
                error = data.get("error", "Unknown error")
                log_test("Stability AI Integration", "FAIL", f"API returned error: {error}")
                return False, "api_error"
        else:
            log_test("Stability AI Integration", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False, "http_error"
            
    except requests.exceptions.Timeout:
        log_test("Stability AI Integration", "FAIL", "Request timed out after 60 seconds")
        return False, "timeout"
    except Exception as e:
        log_test("Stability AI Integration", "FAIL", f"Exception: {str(e)}")
        return False, "exception"

def test_comic_generation_pipeline():
    """Test complete comic generation with real AI images"""
    try:
        # Test story for comic generation
        test_story = {
            "story": "Jamie and Kylee discover a magical crystal in their grandmother's attic. The crystal glows with mystical energy and transports them to an enchanted forest where they meet a wise fairy who gives them a quest to save the magical realm.",
            "title": "Test Real AI Images Comic",
            "style": "Mystical Watercolor",
            "aspect_ratio": "4:5",
            "generate_images": True
        }
        
        print("Testing complete comic generation pipeline - this may take 2-3 minutes...")
        response = requests.post(
            f"{BACKEND_URL}/parse-story", 
            json=test_story, 
            timeout=180,  # 3 minutes for full comic generation
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify comic structure
            if "panels" in data and "id" in data:
                panels = data["panels"]
                comic_id = data["id"]
                title = data.get("title", "Unknown")
                
                # Check each panel for real images
                real_images = 0
                total_panels = len(panels)
                total_image_size = 0
                
                for i, panel in enumerate(panels):
                    panel_num = panel.get("panel", i+1)
                    image_base64 = panel.get("image_base64")
                    scene = panel.get("scene", "No scene")
                    dialogue = panel.get("dialogue", "No dialogue")
                    
                    if image_base64:
                        image_size = len(image_base64)
                        total_image_size += image_size
                        
                        # Real AI images should be substantial even after compression
                        if image_size > 500000:  # 500KB threshold for compressed real images
                            real_images += 1
                            print(f"    Panel {panel_num}: Real AI image ({image_size:,} bytes)")
                        elif image_size > 100000:  # Smaller but potentially real
                            real_images += 1
                            print(f"    Panel {panel_num}: Compressed AI image ({image_size:,} bytes)")
                        else:
                            print(f"    Panel {panel_num}: Likely placeholder ({image_size:,} bytes)")
                    else:
                        print(f"    Panel {panel_num}: No image data")
                
                # Evaluate results
                if real_images == total_panels and total_panels > 0:
                    log_test("Comic Generation Pipeline", "PASS", 
                           f"Generated {total_panels} panels, all with real AI images. Total size: {total_image_size:,} bytes. Comic ID: {comic_id}")
                    return True, comic_id
                elif real_images > 0:
                    log_test("Comic Generation Pipeline", "WARNING", 
                           f"Generated {total_panels} panels, {real_images} with real images, {total_panels-real_images} with placeholders")
                    return True, comic_id
                else:
                    log_test("Comic Generation Pipeline", "FAIL", 
                           f"Generated {total_panels} panels, but no real AI images detected")
                    return False, None
            else:
                log_test("Comic Generation Pipeline", "FAIL", "Invalid response structure")
                return False, None
        else:
            log_test("Comic Generation Pipeline", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False, None
            
    except requests.exceptions.Timeout:
        log_test("Comic Generation Pipeline", "FAIL", "Request timed out after 3 minutes")
        return False, None
    except Exception as e:
        log_test("Comic Generation Pipeline", "FAIL", f"Exception: {str(e)}")
        return False, None

def test_comic_retrieval(comic_id):
    """Test retrieving a saved comic with images intact"""
    if not comic_id:
        log_test("Comic Retrieval", "SKIP", "No comic ID provided")
        return False
        
    try:
        response = requests.get(f"{BACKEND_URL}/comics/{comic_id}", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if "panels" in data and "id" in data:
                panels = data["panels"]
                title = data.get("title", "Unknown")
                
                # Verify images are still intact
                panels_with_images = 0
                total_size = 0
                
                for panel in panels:
                    if panel.get("image_base64"):
                        panels_with_images += 1
                        total_size += len(panel["image_base64"])
                
                if panels_with_images > 0:
                    log_test("Comic Retrieval", "PASS", 
                           f"Retrieved comic '{title}' with {panels_with_images}/{len(panels)} panels having images. Total size: {total_size:,} bytes")
                    return True
                else:
                    log_test("Comic Retrieval", "FAIL", "Retrieved comic has no image data")
                    return False
            else:
                log_test("Comic Retrieval", "FAIL", "Invalid comic structure")
                return False
        elif response.status_code == 404:
            log_test("Comic Retrieval", "FAIL", "Comic not found in database")
            return False
        else:
            log_test("Comic Retrieval", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        log_test("Comic Retrieval", "FAIL", f"Exception: {str(e)}")
        return False

def test_comics_list():
    """Test retrieving list of all comics"""
    try:
        response = requests.get(f"{BACKEND_URL}/comics", timeout=30)
        
        if response.status_code == 200:
            comics = response.json()
            
            if isinstance(comics, list):
                log_test("Comics List", "PASS", f"Retrieved {len(comics)} comics from database")
                
                # Show recent comics with image info
                for comic in comics[-3:]:  # Show last 3 comics
                    title = comic.get("title", "Unknown")
                    panels = comic.get("panels", [])
                    panels_with_images = sum(1 for p in panels if p.get("image_base64"))
                    print(f"    Comic: '{title}' - {panels_with_images}/{len(panels)} panels with images")
                
                return True
            else:
                log_test("Comics List", "FAIL", "Response is not a list")
                return False
        else:
            log_test("Comics List", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        log_test("Comics List", "FAIL", f"Exception: {str(e)}")
        return False

def check_backend_logs():
    """Check backend logs for Stability AI success messages"""
    try:
        # Check supervisor logs for backend
        log_files = [
            "/var/log/supervisor/backend.out.log",
            "/var/log/supervisor/backend.err.log"
        ]
        
        stability_success_found = False
        mongodb_errors_found = False
        
        for log_file in log_files:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    content = f.read()
                    
                    # Look for Stability AI success messages
                    if "Successfully generated Stability AI image" in content:
                        stability_success_found = True
                    
                    # Look for MongoDB document size errors
                    if "BSON document too large" in content or "document too large" in content:
                        mongodb_errors_found = True
        
        if stability_success_found and not mongodb_errors_found:
            log_test("Backend Logs Check", "PASS", "Found Stability AI success messages, no MongoDB size errors")
            return True
        elif stability_success_found and mongodb_errors_found:
            log_test("Backend Logs Check", "WARNING", "Found Stability AI success but also MongoDB size errors")
            return True
        elif not stability_success_found:
            log_test("Backend Logs Check", "FAIL", "No Stability AI success messages found in logs")
            return False
        else:
            log_test("Backend Logs Check", "WARNING", "Could not access backend logs")
            return False
            
    except Exception as e:
        log_test("Backend Logs Check", "WARNING", f"Could not check logs: {str(e)}")
        return False

def main():
    """Run comprehensive backend tests"""
    print("=" * 80)
    print("MYSTICAL WHISPERS COMICS - BACKEND TESTING")
    print("Focus: Real AI Image Generation and Comic Pipeline")
    print("=" * 80)
    print()
    
    results = {}
    
    # Test 1: API Health
    results['api_health'] = test_api_health()
    
    # Test 2: Stability AI Integration (Priority Test)
    results['stability_ai'], image_type = test_stability_ai_integration()
    
    # Test 3: Comic Generation Pipeline (Priority Test)
    results['comic_generation'], comic_id = test_comic_generation_pipeline()
    
    # Test 4: Comic Retrieval (Priority Test)
    results['comic_retrieval'] = test_comic_retrieval(comic_id)
    
    # Test 5: Comics List
    results['comics_list'] = test_comics_list()
    
    # Test 6: Backend Logs Check
    results['logs_check'] = check_backend_logs()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    print()
    
    # Priority test results
    priority_tests = ['stability_ai', 'comic_generation', 'comic_retrieval']
    priority_passed = sum(1 for test in priority_tests if results.get(test, False))
    
    print("PRIORITY TEST RESULTS:")
    for test in priority_tests:
        status = "✅ PASS" if results.get(test, False) else "❌ FAIL"
        test_name = test.replace('_', ' ').title()
        print(f"  {status} {test_name}")
    
    print()
    print(f"Priority Tests Passed: {priority_passed}/{len(priority_tests)}")
    
    if priority_passed == len(priority_tests):
        print("\n🎉 ALL PRIORITY TESTS PASSED - Real AI images are working!")
    elif priority_passed > 0:
        print(f"\n⚠️  PARTIAL SUCCESS - {priority_passed} out of {len(priority_tests)} priority tests passed")
    else:
        print("\n❌ CRITICAL FAILURE - No priority tests passed")
    
    return results

if __name__ == "__main__":
    main()