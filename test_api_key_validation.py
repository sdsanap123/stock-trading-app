#!/usr/bin/env python3
"""
Test script for API key validation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from components.groq_analyzer import GroqNewsAnalyzer
from components.gemini_analyzer import GeminiAIAnalyzer

def test_groq_api_key_validation():
    """Test Groq API key validation."""
    print("🧪 Testing Groq API Key Validation...")
    
    # Initialize analyzer
    groq_analyzer = GroqNewsAnalyzer()
    
    # Test with empty key
    print("📝 Testing empty API key...")
    result = groq_analyzer.set_api_key("")
    print(f"Empty key result: {result}")
    
    # Test with invalid key
    print("📝 Testing invalid API key...")
    result = groq_analyzer.set_api_key("invalid_key_123")
    print(f"Invalid key result: {result}")
    
    # Test with valid format but invalid key
    print("📝 Testing invalid but valid format API key...")
    result = groq_analyzer.set_api_key("gsk_invalid_key_123456789")
    print(f"Invalid format key result: {result}")
    
    print("✅ Groq API key validation tests completed!")

def test_gemini_api_key_validation():
    """Test Gemini API key validation."""
    print("\n🧪 Testing Gemini API Key Validation...")
    
    # Initialize analyzer
    gemini_analyzer = GeminiAIAnalyzer()
    
    # Test with empty key
    print("📝 Testing empty API key...")
    result = gemini_analyzer.set_api_key("")
    print(f"Empty key result: {result}")
    
    # Test with invalid key
    print("📝 Testing invalid API key...")
    result = gemini_analyzer.set_api_key("invalid_key_123")
    print(f"Invalid key result: {result}")
    
    # Test with valid format but invalid key
    print("📝 Testing invalid but valid format API key...")
    result = gemini_analyzer.set_api_key("AIzaSyInvalidKey123456789")
    print(f"Invalid format key result: {result}")
    
    print("✅ Gemini API key validation tests completed!")

def test_fallback_system():
    """Test the fallback system."""
    print("\n🧪 Testing Fallback System...")
    
    # Test Groq fallback to Gemini
    groq_analyzer = GroqNewsAnalyzer()
    print("📝 Testing Groq fallback to Gemini...")
    
    try:
        gemini_fallback = groq_analyzer._get_gemini_fallback()
        if gemini_fallback:
            print("✅ Groq fallback to Gemini: Success")
        else:
            print("❌ Groq fallback to Gemini: Failed")
    except Exception as e:
        print(f"❌ Groq fallback to Gemini: Error - {str(e)}")
    
    # Test Gemini fallback to Groq
    gemini_analyzer = GeminiAIAnalyzer()
    print("📝 Testing Gemini fallback to Groq...")
    
    try:
        groq_fallback = gemini_analyzer._get_groq_fallback()
        if groq_fallback:
            print("✅ Gemini fallback to Groq: Success")
        else:
            print("❌ Gemini fallback to Groq: Failed")
    except Exception as e:
        print(f"❌ Gemini fallback to Groq: Error - {str(e)}")
    
    print("✅ Fallback system tests completed!")

if __name__ == "__main__":
    print("🚀 Starting API Key Validation Tests...\n")
    
    try:
        test_groq_api_key_validation()
        test_gemini_api_key_validation()
        test_fallback_system()
        
        print("\n🎉 All API key validation tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
