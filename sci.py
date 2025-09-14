from flask import Flask, render_template, request, jsonify
from google import genai
import json
import os

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Initialize Gemini API client
client = genai.Client(api_key="AIzaSyC8Jpsr36NM-YEQjLR9sIg3-EYaCskLQJs")

# Science City Kolkata data
SCIENCE_CITY_DATA = {
    "name": "Science City Kolkata",
    "location": "Kolkata, West Bengal, India",
    "hours": {
        "Tuesday-Sunday": "9:00 AM - 8:00 PM",
        "Monday": "Closed"
    },
    "ticket_prices": {
        "Adults": "₹60",
        "Children (below 5 years)": "Free",
        "Students": "₹50",
        "Seniors (60+)": "₹50",
        "Space Theater": "₹50 additional"
    },
    "facilities": {
        "restrooms": {
            "main_building": "Near the main entrance",
            "science_park": "Next to the evolution park"
        },
        "cafe": {
            "location": "Ground floor, near space theater",
            "hours": "10:00 AM - 7:00 PM"
        },
        "gift_shop": {
            "location": "Ground floor, near exit",
            "hours": "9:30 AM - 7:30 PM"
        },
        "parking": {
            "location": "Main entrance area",
            "capacity": "200 cars",
            "fee": "₹30 for 4 hours"
        }
    },
    "attractions": {
        "space_odyssey": {
            "name": "Space Odyssey",
            "description": "India's first large format theater with shows about space and astronomy",
            "show_times": ["11:00 AM", "1:00 PM", "3:00 PM", "5:00 PM"]
        },
        "dynamotion": {
            "name": "Dynamotion",
            "description": "Hall with interactive exhibits demonstrating scientific principles"
        },
        "evolution_park": {
            "name": "Evolution Theme Park",
            "description": "Outdoor park tracing the story of evolution from big bang to modern humans"
        },
        "maritime_center": {
            "name": "Maritime Center",
            "description": "Exhibits showcasing India's maritime heritage and technology"
        },
        "earth_exploration": {
            "name": "Earth Exploration Hall",
            "description": "Exhibits focused on earth sciences, geology, and natural phenomena"
        }
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
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Create the HTML template
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Science City Kolkata - AI Assistant</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background: linear-gradient(135deg, #0c2461 0%, #1e3799 30%, #4a69bd 70%, #6a89cc 100%);
            color: #333;
            line-height: 1.6;
            min-height: 100vh;
            overflow: hidden;
        }
        
        .chatbot-container {
            width: 100%;
            height: 100vh;
            background: white;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .chatbot-header {
            background: linear-gradient(135deg, #4a69bd 0%, #1e3799 100%);
            color: white;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .chatbot-header h1 {
            margin: 0;
            font-size: 24px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .chatbot-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 15px;
            background: #f8f9fa;
        }
        
        .message {
            max-width: 80%;
            padding: 12px 18px;
            border-radius: 18px;
            margin-bottom: 10px;
            animation: fadeIn 0.3s ease;
        }
        
        .user-message {
            align-self: flex-end;
            background: #4a69bd;
            color: white;
            border-bottom-right-radius: 5px;
        }
        
        .bot-message {
            align-self: flex-start;
            background: white;
            color: #333;
            border: 1px solid #e9ecef;
            border-bottom-left-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        
        .typing-indicator {
            display: inline-flex;
            align-items: center;
            height: 20px;
        }
        
        .typing-indicator span {
            height: 8px;
            width: 8px;
            background: #888;
            border-radius: 50%;
            display: inline-block;
            margin: 0 2px;
            animation: typing 1.2s infinite;
        }
        
        .typing-indicator span:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing-indicator span:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        .chatbot-input {
            display: flex;
            padding: 20px;
            border-top: 1px solid #eee;
            background: white;
        }
        
        #chatbot-input-field {
            flex: 1;
            padding: 12px 18px;
            border: 1px solid #ddd;
            border-radius: 25px;
            outline: none;
            font-size: 16px;
        }
        
        #chatbot-input-field:focus {
            border-color: #4a69bd;
            box-shadow: 0 0 0 2px rgba(74, 105, 189, 0.2);
        }
        
        #chatbot-send-btn {
            background: #4a69bd;
            color: white;
            border: none;
            border-radius: 25px;
            padding: 12px 20px;
            margin-left: 10px;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        #chatbot-send-btn:hover {
            background: #1e3799;
        }
        
        /* Animations */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes typing {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-5px); }
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .chatbot-header h1 {
                font-size: 20px;
            }
            
            .chatbot-input {
                padding: 15px;
            }
            
            #chatbot-input-field {
                padding: 10px 15px;
                font-size: 14px;
            }
            
            #chatbot-send-btn {
                padding: 10px 15px;
                font-size: 14px;
            }
        }
        
        .suggested-questions {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            padding: 0 20px 15px;
            background: #f8f9fa;
            border-bottom: 1px solid #eee;
        }
        
        .suggestion-btn {
            background: white;
            color: #4a69bd;
            border: 1px solid #4a69bd;
            border-radius: 20px;
            padding: 8px 15px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
        }
        
        .suggestion-btn:hover {
            background: #4a69bd;
            color: white;
        }
    </style>
</head>
<body>
    <!-- Chatbot Container -->
    <div class="chatbot-container">
        <div class="chatbot-header">
            <h1>🔬 Science City Kolkata Assistant</h1>
        </div>
        
        <div class="suggested-questions">
            <button class="suggestion-btn" onclick="setQuestion('What are the opening hours?')">Opening Hours</button>
            <button class="suggestion-btn" onclick="setQuestion('What are the ticket prices?')">Ticket Prices</button>
            <button class="suggestion-btn" onclick="setQuestion('Where is the space theater?')">Space Theater</button>
            <button class="suggestion-btn" onclick="setQuestion('Is there parking available?')">Parking Info</button>
        </div>
        
        <div class="chatbot-messages">
            <div class="message bot-message">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>
        <div class="chatbot-input">
            <input type="text" placeholder="Ask about Science City Kolkata..." id="chatbot-input-field">
            <button id="chatbot-send-btn">Send</button>
        </div>
    </div>

    <script>
        // Chatbot functionality
        document.addEventListener('DOMContentLoaded', function() {
            const messagesContainer = document.querySelector('.chatbot-messages');
            const inputField = document.getElementById('chatbot-input-field');
            const sendBtn = document.getElementById('chatbot-send-btn');
            
            // Function to add a message to the chat
            function addMessage(text, isUser = false) {
                const messageDiv = document.createElement('div');
                messageDiv.classList.add('message');
                messageDiv.classList.add(isUser ? 'user-message' : 'bot-message');
                messageDiv.textContent = text;
                messagesContainer.appendChild(messageDiv);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
            
            // Function to show typing indicator
            function showTypingIndicator() {
                const typingDiv = document.createElement('div');
                typingDiv.classList.add('message', 'bot-message');
                typingDiv.innerHTML = `
                    <div class="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                `;
                typingDiv.id = 'typing-indicator';
                messagesContainer.appendChild(typingDiv);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
                return typingDiv;
            }
            
            // Function to remove typing indicator
            function removeTypingIndicator() {
                const typingIndicator = document.getElementById('typing-indicator');
                if (typingIndicator) {
                    typingIndicator.remove();
                }
            }
            
            // Function to send message
            function sendMessage() {
                const message = inputField.value.trim();
                if (message) {
                    addMessage(message, true);
                    inputField.value = '';
                    
                    // Show typing indicator
                    showTypingIndicator();
                    
                    // Send to backend
                    fetch('/ask', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            question: message
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        removeTypingIndicator();
                        addMessage(data.answer);
                    })
                    .catch(error => {
                        removeTypingIndicator();
                        addMessage("Sorry, I'm having trouble connecting right now. Please try again later.");
                        console.error('Error:', error);
                    });
                }
            }
            
            // Set question from suggestion
            window.setQuestion = function(question) {
                inputField.value = question;
                sendMessage();
            }
            
            // Send message on button click
            sendBtn.addEventListener('click', sendMessage);
            
            // Send message on Enter key
            inputField.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
            
            // Add welcome message after a short delay
            setTimeout(() => {
                removeTypingIndicator();
                addMessage("Hello! I'm your Science City Kolkata assistant. I can help you with information about opening hours, ticket prices, attractions, and more. How can I help you today?");
            }, 1000);
        });
    </script>
</body>
</html>''')
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
