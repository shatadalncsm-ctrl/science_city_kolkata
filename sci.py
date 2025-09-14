from flask import Flask, render_template, request, jsonify
from google import genai
import json
import os

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Initialize Gemini API client
client = genai.Client(api_key="AIzaSyC8Jpsr36NM-YEQjLR9sIg3-EYaCskLQJs")

# Load Science City data from external JSON file
def load_science_city_data():
    try:
        with open('data/science_city_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback data if file doesn't exist
        return {
            "name": "Science City Kolkata",
            "location": "J.B.S Haldane Avenue, Mirania Gardens, East Topsia, Topsia, Kolkata, West Bengal, 700046, India",
            "hours": {
                "Everyday": "10:00 AM - 7:00 PM"
            },
            "ticket_prices": {
                "Entry Fee (General)": "₹70.00",
                "Entry Fee (Organized Group, min 25)": "₹60.00",
                "Entry Fee (Organized School Groups)": "₹35.00",
                "Entry Fee (Underprivileged Groups)": "₹5.00"
            },
            "attractions": {
                "space_odyssey": {
                    "name": "Space Odyssey",
                    "description": "India's first large format theater with shows about space and astronomy",
                    "show_times": ["11:00 AM", "1:00 PM", "3:00 PM", "5:00 PM"]
                }
            },
            "facilities": {
                "parking": "Ample parking is available for both cars and buses"
            }
        }

def ask_gemini(prompt: str, model="gemini-2.0-flash"):
    """Send prompt to Gemini and get response."""
    try:
        response = client.models.generate_content(model=model, contents=prompt)
        return response.text
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

def get_science_city_answer(question):
    """Get specific answer about Science City."""
    SCIENCE_CITY_DATA = load_science_city_data()
    science_city_context = json.dumps(SCIENCE_CITY_DATA, indent=2)
    
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

if __name__ == '__main__':
    # Create templates and data directories if they don't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
