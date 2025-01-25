import os
import base64
import speech_recognition as sr
from together import Together
import key as key

class Chatbot:
    def __init__(self, api_key):
        self.client = Together(api_key=api_key)
        
    def get_user_input(self, prompt, valid_responses=None):
        """
        Handles user input with validation.
        :param prompt: The prompt text to show to the user.
        :param valid_responses: A list of valid responses (optional).
        :return: The user's input (converted to lowercase and stripped).
        """
        while True:
            user_input = input(prompt).strip().lower()
            if valid_responses and user_input not in valid_responses:
                print(f"Invalid input. Please enter one of the following: {', '.join(valid_responses)}")
            else:
                return user_input

    def chat(self, query):
        """Handles text-based queries."""
        response = self.client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
            messages=[{
                "role": "user",
                "content": query
            }],
            max_tokens=512,
            temperature=0.7,
            top_p=0.7,
            top_k=50,
            repetition_penalty=1,
            stop=["<|eot_id|>"],
        )
        
        print(f"AI: {response.choices[0].message.content}")

    def listen_to_user(self):
        """Listen to user voice command and convert it to text."""
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Listening for your command...")
            audio = recognizer.listen(source)
            try:
                text = recognizer.recognize_google(audio)
                print(f"User said: {text}")
                return text
            except:
                print("Sorry, I didn't catch that.")
                return None

    def display_welcome_message(self):
        """Displays a welcome message and instructions."""
        welcome_message = """
        =============================================================
                               WELCOME TO THE CHATBOT
        =============================================================

        Hello! I'm your virtual assistant, and I'm here to help you
        with two exciting features:

        1. **Text Mode**: Engage in a conversation with me. Ask questions,
           seek information, or just chat!
        2. **Voice Mode**: Engage in a conversation with me using voice commands. Ask questions,
           seek information, or just chat!

        =============================================================
                           How can I assist you today?
        =============================================================
        """
        print(welcome_message)

    def run(self):
        """Runs the main logic of the chatbot."""
        self.display_welcome_message()

        user_input = self.get_user_input(
            "Enter '1' for Text Mode or '2' for Voice Mode: ",
            valid_responses=['1', '2']
        )
        
        if user_input == '1':
            print("\nYou have selected Text Mode.\n")
            while True:
                query = input("Enter your query (type 'exit' to quit): ")
                if query.lower() == "exit":
                    print("Exiting the chat. Have a great day!")
                    break
                self.chat(query)
        
        elif user_input == '2':
            print("\nYou have selected Voice Mode.\n")
            while True:
                print("Say something...")
                query = self.listen_to_user()
                if query:
                    self.chat(query)
                    # Ask if the user wants to continue or exit
                    next_action = self.get_user_input(
                        "Do you want to ask another question? (yes/exit): ",
                        valid_responses=['yes', 'exit']
                    )
                    if next_action == 'exit':
                        print("Exiting the chat. Have a great day!")
                        break

chatbot = Chatbot(api_key=key.key)
chatbot.run()
