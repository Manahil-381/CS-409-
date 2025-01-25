from flask import Flask, request, jsonify
from chatbot import Chatbot
import key  # Assuming the API key is stored in key.py

app = Flask(__name__)

# Initialize the chatbot
chatbot = Chatbot(api_key=key.key)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.form.get('message')
    if user_message:
        chatbot.chat(user_message)  # Chatbot logic
        return jsonify({'response': 'Your message has been received.'})
    return jsonify({'error': 'No message received.'})

def run_flask():
    app.run(debug=False, use_reloader=False)  # Turn off reloader to prevent it from running twice

if __name__ == '__main__':
    run_flask()
