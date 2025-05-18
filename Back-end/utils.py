#!/usr/bin/env python3
"""
Utility script to list available Google Gemini models.
Run this script to see which models are available with your API key.
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv
import json

def main():
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        return
    
    # Configure Google Generative AI
    genai.configure(api_key=api_key)
    
    try:
        # List available models
        models = genai.list_models()
        
        print("\n=== Available Google Gemini Models ===\n")
        
        for model in models:
            if "gemini" in model.name:
                print(f"Name: {model.name}")
                print(f"Display Name: {model.display_name}")
                print(f"Description: {model.description}")
                print(f"Supported Generation Methods:")
                for method in model.supported_generation_methods:
                    print(f"  - {method}")
                print("=" * 40)
        
        print("\nUse one of these model names in your .env file.")
        
    except Exception as e:
        print(f"Error listing models: {str(e)}")

if __name__ == "__main__":
    main() 