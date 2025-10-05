#!/usr/bin/env python3
"""
Enhanced Backend Testing for Mystical Whispers Comics
Focus: Brand Appropriateness, Character Accuracy, and Enhanced Features
"""

import requests
import json
import base64
import time
import os
from datetime import datetime

# Configuration
BACKEND_URL = "https://whisper-comics.preview.emergentagent.com/api"
TEST_TIMEOUT = 120

def log_test(test_name, status, details=""):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"[{timestamp}] {status_symbol} {test_name}: {status}")
    if details:
        print(f"    Details: {details}")
    print()

def test_content_moderation_compliance():
    """Test that image generation avoids inappropriate content"""
    try:
        # Test story with potential for inappropriate content
        test_story = {
            "story": "Jamie and Kylee are getting ready for a mystical ceremony. They choose their sacred robes and prepare their ritual space with candles and crystals. The moonlight streams through the window as they begin their spiritual practice.",
            "title": "Content Moderation Test",
            "style": "Mystical Watercolor",
            "aspect_ratio": "4:5",
            "generate_images": True
        }
        
        print("Testing content moderation compliance - checking for appropriate imagery...")
        response = requests.post(
            f"{BACKEND_URL}/parse-story", 
            json=test_story, 
            timeout=TEST_TIMEOUT,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            panels = data.get("panels", [])
            
            # Check for content moderation flags in logs
            moderation_flags = 0
            successful_generations = 0
            
            for panel in panels:
                if panel.get("image_base64"):
                    image_size = len(panel["image_base64"])
                    if image_size > 100000:  # Real AI image
                        successful_generations += 1
                    else:
                        # Might be placeholder due to moderation
                        moderation_flags += 1
            
            if successful_generations >= len(panels) * 0.8:  # 80% success rate
                log_test("Content Moderation Compliance", "PASS", 
                       f"Generated {successful_generations}/{len(panels)} appropriate images without moderation flags")
                return True
            else:
                log_test("Content Moderation Compliance", "WARNING", 
                       f"Only {successful_generations}/{len(panels)} images generated - possible moderation issues")
                return False
        else:
            log_test("Content Moderation Compliance", "FAIL", f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Content Moderation Compliance", "FAIL", f"Exception: {str(e)}")
        return False

def test_mystical_theme_accuracy():
    """Test that stories include required mystical elements"""
    try:
        # Test story focused on mystical themes
        test_story = {
            "story": "Jamie spreads her tarot cards on the candlelit table while Kylee consults her astrology chart. The full moon illuminates their sacred space filled with crystals and feathers. They seek guidance from their ancestors through ancient rituals.",
            "title": "Mystical Theme Test",
            "style": "Mystical Watercolor", 
            "aspect_ratio": "4:5",
            "generate_images": False  # Focus on story parsing
        }
        
        print("Testing mystical theme accuracy in story parsing...")
        response = requests.post(
            f"{BACKEND_URL}/parse-story",
            json=test_story,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            panels = data.get("panels", [])
            
            # Check for mystical elements in scenes
            mystical_elements = [
                "tarot", "cards", "candles", "crystals", "moon", "astrology", 
                "sacred", "ritual", "feathers", "ancestral", "spiritual", "mystical"
            ]
            
            panels_with_mystical = 0
            total_mystical_mentions = 0
            
            for panel in panels:
                scene = panel.get("scene", "").lower()
                dialogue = panel.get("dialogue", "").lower()
                actions = panel.get("character_actions", "").lower()
                
                panel_mystical_count = 0
                for element in mystical_elements:
                    if element in scene or element in dialogue or element in actions:
                        panel_mystical_count += 1
                
                if panel_mystical_count > 0:
                    panels_with_mystical += 1
                    total_mystical_mentions += panel_mystical_count
            
            if panels_with_mystical >= len(panels) * 0.8:  # 80% of panels should have mystical elements
                log_test("Mystical Theme Accuracy", "PASS", 
                       f"{panels_with_mystical}/{len(panels)} panels contain mystical elements ({total_mystical_mentions} total mentions)")
                return True
            else:
                log_test("Mystical Theme Accuracy", "FAIL", 
                       f"Only {panels_with_mystical}/{len(panels)} panels contain mystical elements")
                return False
        else:
            log_test("Mystical Theme Accuracy", "FAIL", f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Mystical Theme Accuracy", "FAIL", f"Exception: {str(e)}")
        return False

def test_character_references():
    """Test character reference system for Jamie and Kylee"""
    try:
        # Check if character references exist
        response = requests.get(f"{BACKEND_URL}/characters", timeout=30)
        
        if response.status_code == 200:
            characters = response.json()
            
            jamie_found = False
            kylee_found = False
            
            for char in characters:
                name = char.get("name", "").lower()
                description = char.get("description", "")
                has_image = bool(char.get("image_base64"))
                
                if "jamie" in name:
                    jamie_found = True
                    print(f"    Jamie character found: {len(description)} char description, has image: {has_image}")
                elif "kylee" in name:
                    kylee_found = True
                    print(f"    Kylee character found: {len(description)} char description, has image: {has_image}")
            
            if jamie_found and kylee_found:
                log_test("Character References", "PASS", "Both Jamie and Kylee character references found")
                return True
            elif jamie_found or kylee_found:
                missing = "Kylee" if jamie_found else "Jamie"
                log_test("Character References", "WARNING", f"Only found one character reference, missing: {missing}")
                return False
            else:
                log_test("Character References", "FAIL", "No Jamie or Kylee character references found")
                return False
        else:
            log_test("Character References", "FAIL", f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Character References", "FAIL", f"Exception: {str(e)}")
        return False

def test_enhanced_image_parameters():
    """Test that images are generated with enhanced parameters (832x1216, CFG 15, steps 35)"""
    try:
        # Test single image generation to check parameters
        print("Testing enhanced image parameters (may take 60 seconds)...")
        response = requests.get(f"{BACKEND_URL}/test-image", timeout=TEST_TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                image_size = data.get("image_size", 0)
                method = data.get("method", "")
                
                # Enhanced parameters should produce larger, higher quality images
                if image_size > 2000000:  # 2MB+ indicates high quality
                    log_test("Enhanced Image Parameters", "PASS", 
                           f"High quality image generated: {image_size:,} bytes using {method}")
                    return True
                elif image_size > 1000000:  # 1MB+ is still good
                    log_test("Enhanced Image Parameters", "WARNING", 
                           f"Good quality image: {image_size:,} bytes, but could be higher with enhanced parameters")
                    return True
                else:
                    log_test("Enhanced Image Parameters", "FAIL", 
                           f"Low quality image: {image_size:,} bytes - enhanced parameters may not be working")
                    return False
            else:
                log_test("Enhanced Image Parameters", "FAIL", f"Image generation failed: {data.get('error')}")
                return False
        else:
            log_test("Enhanced Image Parameters", "FAIL", f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Enhanced Image Parameters", "FAIL", f"Exception: {str(e)}")
        return False

def test_prompt_enhancement_system():
    """Test the enhanced mystical-focused story parser"""
    try:
        # Test with a simple story to see how it gets enhanced
        simple_story = {
            "story": "Two friends discover something magical and go on an adventure.",
            "title": "Prompt Enhancement Test",
            "style": "Mystical Watercolor",
            "aspect_ratio": "4:5", 
            "generate_images": False
        }
        
        print("Testing prompt enhancement system...")
        response = requests.post(
            f"{BACKEND_URL}/parse-story",
            json=simple_story,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            panels = data.get("panels", [])
            
            # Check if the simple story was enhanced with mystical elements
            enhanced_elements = 0
            mystical_keywords = [
                "jamie", "kylee", "tarot", "candles", "crystals", "sacred", 
                "mystical", "spiritual", "moon", "ritual", "ancestral"
            ]
            
            for panel in panels:
                scene = panel.get("scene", "").lower()
                dialogue = panel.get("dialogue", "").lower()
                
                for keyword in mystical_keywords:
                    if keyword in scene or keyword in dialogue:
                        enhanced_elements += 1
                        break  # Count each panel only once
            
            if enhanced_elements >= len(panels) * 0.6:  # 60% should be enhanced
                log_test("Prompt Enhancement System", "PASS", 
                       f"Simple story enhanced with mystical elements in {enhanced_elements}/{len(panels)} panels")
                return True
            else:
                log_test("Prompt Enhancement System", "FAIL", 
                       f"Story not properly enhanced - only {enhanced_elements}/{len(panels)} panels have mystical elements")
                return False
        else:
            log_test("Prompt Enhancement System", "FAIL", f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Prompt Enhancement System", "FAIL", f"Exception: {str(e)}")
        return False

def test_brand_guidelines_compliance():
    """Test overall brand guidelines compliance"""
    try:
        # Test story that could potentially violate brand guidelines
        test_story = {
            "story": "Jamie and Kylee prepare for their evening ritual. They light candles, arrange crystals, and consult their tarot deck under the moonlight. Their sacred space glows with mystical energy as they connect with ancient wisdom.",
            "title": "Brand Guidelines Test",
            "style": "Mystical Watercolor",
            "aspect_ratio": "4:5",
            "generate_images": True
        }
        
        print("Testing brand guidelines compliance...")
        response = requests.post(
            f"{BACKEND_URL}/parse-story",
            json=test_story,
            timeout=TEST_TIMEOUT,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            panels = data.get("panels", [])
            
            # Check for brand compliance indicators
            brand_compliant_panels = 0
            total_image_size = 0
            
            for panel in panels:
                scene = panel.get("scene", "").lower()
                image_base64 = panel.get("image_base64")
                
                # Check for appropriate mystical themes
                has_mystical_theme = any(word in scene for word in [
                    "sacred", "mystical", "spiritual", "candles", "crystals", "tarot", "moon"
                ])
                
                # Check for modest/appropriate descriptions
                has_appropriate_content = not any(word in scene for word in [
                    "revealing", "sexy", "naked", "inappropriate", "cleavage"
                ])
                
                # Check for real AI image
                has_quality_image = image_base64 and len(image_base64) > 200000
                
                if has_mystical_theme and has_appropriate_content and has_quality_image:
                    brand_compliant_panels += 1
                    total_image_size += len(image_base64) if image_base64 else 0
            
            compliance_rate = brand_compliant_panels / len(panels) if panels else 0
            
            if compliance_rate >= 0.8:  # 80% compliance
                log_test("Brand Guidelines Compliance", "PASS", 
                       f"{brand_compliant_panels}/{len(panels)} panels fully compliant. Total image size: {total_image_size:,} bytes")
                return True
            else:
                log_test("Brand Guidelines Compliance", "WARNING", 
                       f"Only {brand_compliant_panels}/{len(panels)} panels fully compliant")
                return False
        else:
            log_test("Brand Guidelines Compliance", "FAIL", f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Brand Guidelines Compliance", "FAIL", f"Exception: {str(e)}")
        return False

def main():
    """Run enhanced backend tests for brand appropriateness and character accuracy"""
    print("=" * 80)
    print("MYSTICAL WHISPERS COMICS - ENHANCED BACKEND TESTING")
    print("Focus: Brand Appropriateness, Character Accuracy, Enhanced Features")
    print("=" * 80)
    print()
    
    results = {}
    
    # Enhanced Tests
    print("🔍 PRIORITY TESTS - BRAND APPROPRIATENESS & ENHANCED FEATURES")
    print("-" * 60)
    
    # Test 1: Content Moderation
    results['content_moderation'] = test_content_moderation_compliance()
    
    # Test 2: Mystical Theme Accuracy  
    results['mystical_themes'] = test_mystical_theme_accuracy()
    
    # Test 3: Character References
    results['character_refs'] = test_character_references()
    
    # Test 4: Enhanced Image Parameters
    results['enhanced_params'] = test_enhanced_image_parameters()
    
    # Test 5: Prompt Enhancement
    results['prompt_enhancement'] = test_prompt_enhancement_system()
    
    # Test 6: Brand Guidelines
    results['brand_compliance'] = test_brand_guidelines_compliance()
    
    # Summary
    print("=" * 80)
    print("ENHANCED TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"Enhanced Tests Passed: {passed}/{total}")
    print()
    
    # Priority test results
    priority_tests = ['content_moderation', 'mystical_themes', 'enhanced_params', 'brand_compliance']
    priority_passed = sum(1 for test in priority_tests if results.get(test, False))
    
    print("PRIORITY ENHANCED TEST RESULTS:")
    for test in priority_tests:
        status = "✅ PASS" if results.get(test, False) else "❌ FAIL"
        test_name = test.replace('_', ' ').title()
        print(f"  {status} {test_name}")
    
    print()
    print(f"Priority Enhanced Tests Passed: {priority_passed}/{len(priority_tests)}")
    
    if priority_passed == len(priority_tests):
        print("\n🎉 ALL PRIORITY ENHANCED TESTS PASSED - Brand guidelines are being followed!")
    elif priority_passed > 0:
        print(f"\n⚠️  PARTIAL SUCCESS - {priority_passed} out of {len(priority_tests)} priority tests passed")
    else:
        print("\n❌ CRITICAL FAILURE - Brand guidelines may not be properly implemented")
    
    return results

if __name__ == "__main__":
    main()