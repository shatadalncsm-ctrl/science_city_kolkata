from flask import Flask, render_template, request, jsonify
from google import genai
from google.api_core import exceptions
import json
import os
import re

# Import API keys from external file
try:
    from api_keys import GEMINI_API_KEYS
except ImportError:
    # Fallback if api_keys.py doesn't exist
    GEMINI_API_KEYS = ["AIzaSyC8Jpsr36NM-YEQjLR9sIg3-EYaCskLQJs"]

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Track current API key index and usage
current_key_index = 0
key_usage_count = {key: 0 for key in GEMINI_API_KEYS}
key_error_count = {key: 0 for key in GEMINI_API_KEYS}
MAX_ERRORS_PER_KEY = 5  # Switch key after this many errors
MAX_REQUESTS_PER_KEY = 1000  # Approximate limit before potential quota issues

# Initialize Gemini API client with first key
client = genai.Client(api_key=GEMINI_API_KEYS[current_key_index])

# Load Science City data from external JSON file
def load_science_city_data():
    try:
        with open('data/science_city_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback data if file doesn't exist
        return {
            "name": "Science City Kolkata",
            "location": "J.B.S Haldane Avenue, Kolkata",
            "hours": {"Everyday": "10:00 AM - 7:00 PM"},
            "ticket_prices": {
                "Entry Fee (General)": "₹70.00",
                "Entry Fee (Organized School Groups)": "₹35.00"
            }
        }

def rotate_api_key():
    """Switch to the next available API key"""
    global current_key_index, client
    
    current_key_index = (current_key_index + 1) % len(GEMINI_API_KEYS)
    new_key = GEMINI_API_KEYS[current_key_index]
    
    print(f"Switching to API key index {current_key_index}")
    client = genai.Client(api_key=new_key)
    
    return new_key

def is_science_related(question):
    """Check if the question is related to science"""
    science_keywords = [
        'science', 'physics', 'chemistry', 'biology', 'astronomy', 'space',
        'technology', 'math', 'mathematics', 'engineering', 'experiment',
        'research', 'discovery', 'invention', 'scientist', 'theory',
        'evolution', 'planet', 'star', 'galaxy', 'atom', 'molecule',
        'cell', 'dna', 'genetic', 'energy', 'force', 'motion', 'electric',
        'magnet', 'light', 'sound', 'heat', 'temperature', 'climate',
        'environment', 'ecology', 'geology', 'volcano', 'earthquake',
        'computer', 'robot', 'ai', 'artificial intelligence', 'machine',
        'laboratory', 'microscope', 'telescope', 'observatory'
    ]
    
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in science_keywords)

def ask_gemini(prompt: str, model="gemini-2.0-flash"):
    """Send prompt to Gemini with API key fallback"""
    global current_key_index, key_usage_count, key_error_count
    
    current_key = GEMINI_API_KEYS[current_key_index]
    key_usage_count[current_key] += 1
    
    # Rotate key if we've hit the request limit
    if key_usage_count[current_key] >= MAX_REQUESTS_PER_KEY:
        print(f"Key {current_key_index} reached request limit, rotating...")
        rotate_api_key()
        current_key = GEMINI_API_KEYS[current_key_index]
    
    try:
        response = client.models.generate_content(model=model, contents=prompt)
        return response.text
        
    except exceptions.ResourceExhausted as e:
        print(f"Quota exceeded for key {current_key_index}: {e}")
        key_error_count[current_key] += 1
        
        if key_error_count[current_key] >= MAX_ERRORS_PER_KEY:
            print(f"Key {current_key_index} has too many errors, rotating...")
            rotate_api_key()
            
        return "I'm currently experiencing high demand. Please try again in a moment."
        
    except exceptions.PermissionDenied as e:
        print(f"Permission denied for key {current_key_index}: {e}")
        key_error_count[current_key] += 1
        
        if key_error_count[current_key] >= MAX_ERRORS_PER_KEY:
            print(f"Key {current_key_index} has permission issues, rotating...")
            rotate_api_key()
            
        return "Service temporarily unavailable. Please try again shortly."
        
    except exceptions.InvalidArgument as e:
        print(f"Invalid API key {current_key_index}: {e}")
        key_error_count[current_key] += 1
        
        if key_error_count[current_key] >= MAX_ERRORS_PER_KEY:
            print(f"Key {current_key_index} is invalid, rotating...")
            rotate_api_key()
            
        return "Service configuration issue. Please try again later."
        
    except Exception as e:
        print(f"Unexpected error with key {current_key_index}: {e}")
        return f"Sorry, I encountered an error: {str(e)}"

def get_science_city_answer(question):
    """Get specific answer about Science City or general science answer."""
    SCIENCE_CITY_DATA = load_science_city_data()
    science_city_context = json.dumps(SCIENCE_CITY_DATA, indent=2)
    
    # Check if question is specifically about Science City Kolkata
    science_city_keywords = [
        'science city', 'kolkata', 'opening', 'hour', 'time', 'ticket', 'price',
        'cost', 'fee', 'attraction', 'exhibit', 'show', 'theater', 'parking',
        'location', 'address', 'how to reach', 'direction', 'facility', 'amenity',
        'restaurant', 'food', 'cafe', 'shop', 'store', 'gift', 'souvenir'
    ]
    
    question_lower = question.lower()
    is_science_city_question = any(keyword in question_lower for keyword in science_city_keywords)
    
    if is_science_city_question:
        # Answer based on Science City data
        prompt = f"""
        You are a knowledgeable guide at Science City Kolkata. 
        Answer the following question based ONLY on the Science City information provided.
        
        SCIENCE CITY INFORMATION:
        {science_city_context}
        
        QUESTION: {question}
        
        Instructions:
        1. Be direct, concise and factual
        2. Provide specific location details if applicable
        3. If information is not available, say "I don't have that information"
        4. Keep response under 3 sentences
        """
    elif is_science_related(question):
        # Answer general science questions
        prompt = f"""
        You are a helpful science educator. Answer the following science question:
        
        QUESTION: {question}
        
        Instructions:
        1. Provide accurate, educational information
        2. Explain concepts clearly and simply
        3. Keep response concise but informative
        4. If you don't know the answer, say so
        """
    else:
        # For non-science questions
        return "I'm specialized in Science City Kolkata and general science topics. I'd be happy to help with questions about Science City, its exhibits, or any science-related topics!"
    
    answer = ask_gemini(prompt)
    return answer

@app.route('/')
def index():
    """Render the chatbot page."""
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask_question():
    """Handle question asking."""
    data = request.json
    question = data.get('question', '')
    
    if not question:
        return jsonify({'error': 'No question provided'})
    
    answer = get_science_city_answer(question)
    return jsonify({'answer': answer})

@app.route('/status')
def api_status():
    """Endpoint to check API key status"""
    status = {
        'current_key_index': current_key_index,
        'key_usage': key_usage_count,
        'key_errors': key_error_count,
        'total_keys': len(GEMINI_API_KEYS)
    }
    return jsonify(status)

if __name__ == '__main__':
    # Create templates and data directories if they don't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
