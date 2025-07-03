from flask import Flask, render_template, request, jsonify
import requests
import markdown
from markupsafe import escape

app = Flask(__name__)

# Configuration
API_URL = "API_URL"
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": "Bearer TOKEN"
}
# Initial system message
messages = [
    {
        "role": "system",
        "content": """You are a **friendly and expert personal finance assistant** that provides:
- Clear, actionable budgeting advice
- Personalized recommendations
- Non-judgmental guidance
Format responses in GitHub-flavored Markdown with headings, lists, and bold text for important concepts."""
    }
]

def get_assistant_response(user_input):
    """Get response from IBM Watsonx.ai API and convert markdown to HTML"""
    # Add user message to conversation
    messages.append({"role": "user", "content": [{"type": "text", "text": user_input}]})
    
    # Prepare request body
    body = {
        "messages": messages,
        "project_id": "b70ae34b-3e22-40c4-9bc3-a8e9cb056921",
        "model_id": "meta-llama/llama-3-3-70b-instruct",
        "frequency_penalty": 0,
        "max_tokens": 2000,
        "presence_penalty": 0,
        "temperature": 0.7,  # Slightly more creative than 0
        "top_p": 1
    }
    
    try:
        response = requests.post(API_URL, headers=HEADERS, json=body)
        response.raise_for_status()
        
        data = response.json()
        assistant_content = data.get('choices', [{}])[0].get('message', {}).get('content', 'No response')
        
        # Convert markdown to HTML and sanitize
        html_content = markdown.markdown(
            assistant_content,
            extensions=[
                'fenced_code',
                'tables',
                'toc'
            ]
        )
        
        # Add assistant response to conversation history
        messages.append({"role": "assistant", "content": assistant_content})
        
        return html_content
        
    except requests.exceptions.RequestException as e:
        return f"<p class='error'>API Error: {escape(str(e))}</p>"
    except Exception as e:
        return f"<p class='error'>System Error: {escape(str(e))}</p>"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    if not user_input or not isinstance(user_input, str):
        return jsonify({"error": "Invalid message"}), 400
    
    # Sanitize user input (handled automatically when rendered as text in JS)
    bot_response = get_assistant_response(user_input)
    return jsonify({"response": bot_response})

@app.route("/new_chat", methods=["POST"])
def new_chat():
    """Reset the conversation"""
    global messages
    messages = [
        {
            "role": "system",
            "content": """You are a **friendly and expert personal finance assistant** that provides:
- Clear, actionable budgeting advice
- Personalized recommendations
- Non-judgmental guidance"""
        }
    ]
    return jsonify({"status": "Conversation reset"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
