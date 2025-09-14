from flask import Flask, render_template, request, jsonify, session
from google import genai
from google.api_core import exceptions
import json
import os
import re
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour session timeout

# Fixed API key - replace with your actual key
GEMINI_API_KEY = "AIzaSyC8Jpsr36NM-YEQjLR9sIg3-EYaCskLQJs"

# Initialize Gemini API client
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Error initializing Gemini client: {e}")
    client = None

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
    """Send prompt to Gemini"""
    if not client:
        return "Service is currently unavailable. Please try again later."
    
    try:
        response = client.models.generate_content(model=model, contents=prompt)
        return response.text
        
    except exceptions.ResourceExhausted as e:
        print(f"Quota exceeded: {e}")
        return "I'm currently experiencing high demand. Please try again in a moment."
        
    except exceptions.PermissionDenied as e:
        print(f"Permission denied: {e}")
        return "Service temporarily unavailable. Please try again shortly."
        
    except exceptions.InvalidArgument as e:
        print(f"Invalid API key: {e}")
        return "Service configuration issue. Please try again later."
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        return f"Sorry, I encountered an error: {str(e)}"

def generate_visit_plan(user_data):
    """Generate a personalized visit plan based on user preferences"""
    SCIENCE_CITY_DATA = load_science_city_data()
    science_city_context = json.dumps(SCIENCE_CITY_DATA, indent=2)
    
    prompt = f"""
    Create a personalized visit plan for Science City Kolkata based on the user's preferences.
    
    SCIENCE CITY INFORMATION:
    {science_city_context}
    
    USER PREFERENCES:
    - Interests: {user_data.get('interests', 'Not specified')}
    - Time available: {user_data.get('time_available', 'Not specified')}
    - Start time: {user_data.get('start_time', 'Not specified')}
    - With kids: {user_data.get('with_kids', 'Not specified')}
    - Meal preferences: {user_data.get('meal_preferences', 'Not specified')}
    
    Create a detailed itinerary that includes:
    1. Recommended attractions to visit in order
    2. Suggested timing for each attraction
    3. Meal/snack break suggestions based on their preferences
    4. Estimated time spent at each location
    5. Any special recommendations based on their interests
    
    Make the plan engaging and practical, considering their time constraints.
    """
    
    plan = ask_gemini(prompt)
    return plan

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
    # Initialize session
    session.permanent = True
    session['conversation_state'] = 'welcome'
    session['user_data'] = {}
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask_question():
    """Handle question asking with conversation flow."""
    data = request.json
    question = data.get('question', '')
    current_state = session.get('conversation_state', 'welcome')
    user_data = session.get('user_data', {})
    
    if not question:
        return jsonify({'error': 'No question provided'})
    
    # Handle conversation flow
    if current_state == 'welcome':
        # Welcome message with opening hours and plan trip option
        SCIENCE_CITY_DATA = load_science_city_data()
        opening_hours = SCIENCE_CITY_DATA.get('hours', {}).get('Everyday', '10:00 AM - 7:00 PM')
        
        response = "🔬 Welcome to Science City Kolkata! 🔬\n\n"
        response += f"🕐 **Opening Hours:** {opening_hours}\n\n"
        response += "I can help you with:\n"
        response += "1. 🗓️ Plan your visit (create personalized itinerary)\n"
        response += "2. ℹ️ General information about attractions\n"
        response += "3. 🎫 Ticket pricing information\n"
        response += "4. 🗺️ Directions and how to reach\n\n"
        response += "What would you like assistance with today?"
        session['conversation_state'] = 'main_menu'
    
    elif current_state == 'main_menu':
        # Check if user wants to plan their trip
        if any(word in question.lower() for word in ['plan', 'itinerary', 'visit', '1', 'one', '🗓️']):
            session['conversation_state'] = 'asking_interests'
            response = "Great! Let's plan your visit. What are your main interests? (e.g., space, biology, technology, evolution)"
        else:
            # Handle other questions normally
            response = get_science_city_answer(question)
            # Stay in main_menu state for follow-up questions
    
    elif current_state == 'asking_interests':
        user_data['interests'] = question
        session['user_data'] = user_data
        session['conversation_state'] = 'asking_time'
        response = "Thanks! How much time do you have available for your visit? (e.g., 2 hours, half day, full day)"
    
    elif current_state == 'asking_time':
        user_data['time_available'] = question
        session['user_data'] = user_data
        session['conversation_state'] = 'asking_start_time'
        response = "What time would you like to start your visit? (e.g., 10:00 AM, 1:00 PM)"
    
    elif current_state == 'asking_start_time':
        user_data['start_time'] = question
        session['user_data'] = user_data
        session['conversation_state'] = 'asking_kids'
        response = "Will you be visiting with children? (yes/no)"
    
    elif current_state == 'asking_kids':
        user_data['with_kids'] = question
        session['user_data'] = user_data
        session['conversation_state'] = 'asking_meals'
        response = "Any food preferences for your meal breaks? (e.g., vegetarian, fast food, cafe snacks)"
    
    elif current_state == 'asking_meals':
        user_data['meal_preferences'] = question
        session['user_data'] = user_data
        session['conversation_state'] = 'generating_plan'
        
        # Generate the personalized plan
        plan = generate_visit_plan(user_data)
        response = f"Perfect! Here's your personalized plan for Science City Kolkata:\n\n{plan}\n\nEnjoy your visit! 🎉"
        
        # Reset for next conversation
        session['conversation_state'] = 'main_menu'
    
    else:
        response = get_science_city_answer(question)
    
    return jsonify({'answer': response, 'state': session.get('conversation_state', 'main_menu')})

@app.route('/plan_trip', methods=['POST'])
def start_trip_planning():
    """Start the trip planning process"""
    session['conversation_state'] = 'asking_interests'
    session['user_data'] = {}
    return jsonify({'answer': "Great! Let's plan your visit. What are your main interests? (e.g., space, biology, technology, evolution)", 'state': 'asking_interests'})

@app.route('/reset', methods=['POST'])
def reset_conversation():
    """Reset the conversation state"""
    session['conversation_state'] = 'welcome'
    session['user_data'] = {}
    return jsonify({'status': 'reset'})

@app.route('/status')
def api_status():
    """Endpoint to check API status"""
    status = {
        'status': 'active' if client else 'inactive',
        'service': 'Science City Kolkata Assistant',
        'conversation_state': session.get('conversation_state', 'welcome')
    }
    return jsonify(status)

if __name__ == '__main__':
    # Create necessary directories if they don't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
