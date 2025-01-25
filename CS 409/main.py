from flask import Flask, jsonify, request
import speech_recognition as sr
from together import Together
import os
import datetime
import re
from kivy.lang import Builder
from kivy.clock import Clock
from kivymd.app import MDApp 
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivy.core.window import Window
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty
from kivymd.uix.card import MDCard
from kivymd.uix.navigationdrawer import MDNavigationDrawer
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivymd.uix.gridlayout import MDGridLayout

# Initialize Flask
app = Flask(__name__)

# Initialize Together AI client
try:
    import key
    together_client = Together(api_key=key.key)
except Exception as e:
    print(f"Warning: Together AI key not found or error occurred: {str(e)}")
    together_client = None

# Define screen classes
class SplashPage(MDScreen):
    pass

class LoginPage(MDScreen):
    pass

class SignupPage(MDScreen):
    pass

class ChatPage(MDScreen):
    pass

# Update the ChatBubble class
class ChatBubble(MDCard):
    message = StringProperty()
    is_user = BooleanProperty()
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.adaptive_height = True
        self.size_hint_x = 0.7
        Clock.schedule_once(self.adjust_position)
    
    def adjust_position(self, *args):
        if self.is_user:
            # User messages on right
            #self.parent.add_widget(MDBoxLayout(size_hint_x=0.3))  # Spacer on left
            self.pos_hint = {'right': 0.95}
            self.md_bg_color = [0.6, 0.2, 0.8, 1]  # Purple color
        else:
            # Bot messages on left
            #self.parent.add_widget(Widget(size_hint_x=0.3))  # Spacer on right
            self.pos_hint = {'x': 0.02}
            self.md_bg_color = [0.9, 0.9, 0.9, 1] 

class SideBar(MDNavigationDrawer):
    pass

class ChatApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.accent_palette = "Teal"
        self.theme_cls.theme_style = "Light"
        self.sidebar = None
        Window.bind(on_request_close=self.on_request_close)
        
    def build(self):
        return Builder.load_string(KV)
    
    def on_start(self):
        # Initialize sidebar
        self.sidebar = SideBar()
        # Start with splash screen
        self.root.current = "splash"

    def on_request_close(self, *args):
        return False
    
    def show_login_page(self, *args):
        self.root.current = "main"
    
    def toggle_theme(self):
        self.theme_cls.theme_style = "Dark" if self.theme_cls.theme_style == "Light" else "Light"
    
    def open_sidebar(self):
        if not self.sidebar.parent:
            Window.add_widget(self.sidebar)
        self.sidebar.set_state("open")
    
    def add_message_bubble(self, message, is_user=True):
        chat_list = self.root.get_screen('chat').ids.chat_list
        
        # Create a wrapper layout for the bubble
        wrapper = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),  # Will be adjusted automatically
            adaptive_height=True
        )
        
        # Create and add the bubble
        bubble = ChatBubble(
            message=message,
            is_user=is_user,
        )
        
        if is_user:
            # For user messages, add space on left
            wrapper.add_widget(Widget(size_hint_x=0.3))
            wrapper.add_widget(bubble)
        else:
            # For bot messages, add space on right
            wrapper.add_widget(bubble)
            wrapper.add_widget(Widget(size_hint_x=0.3))
        
        chat_list.add_widget(wrapper)
        
        # Scroll to the bottom
        chat_scroll = self.root.get_screen('chat').ids.chat_scroll
        Clock.schedule_once(lambda dt: setattr(chat_scroll, 'scroll_y', 0))

    def show_error_dialog(self, title, text):
        try:
            dialog = MDDialog(
                title=title,
                text=text,
                size_hint=(0.8, 0.4)
            )
            dialog.open()
        except Exception as e:
            print(f"Dialog error: {str(e)}")
    
    def login(self):
        try:
            email = self.root.get_screen('main').ids.email.text
            password = self.root.get_screen('main').ids.password.text

            if not re.match(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
                self.show_error_dialog("Invalid Email", "Please enter a valid email address.")
            elif not password:
                self.show_error_dialog("Empty Password", "Password cannot be empty.")
            else:
                self.root.current = "chat"
        except Exception as e:
            self.show_error_dialog("Error", f"Login error: {str(e)}")
    
    def signup(self):
        try:
            signup_screen = self.root.get_screen('signup')
            name = signup_screen.ids.name.text
            email = signup_screen.ids.email.text
            password = signup_screen.ids.password.text
            confirm_password = signup_screen.ids.confirm_password.text

            if not name:
                self.show_error_dialog("Error", "Please enter your full name.")
                return
                
            if not re.match(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
                self.show_error_dialog("Invalid Email", "Please enter a valid email address.")
                return
                
            if len(password) < 6:
                self.show_error_dialog("Invalid Password", "Password must be at least 6 characters long.")
                return
                
            if password != confirm_password:
                self.show_error_dialog("Password Mismatch", "Passwords do not match.")
                return

            self.root.current = "chat"
            
        except Exception as e:
            self.show_error_dialog("Error", f"Signup error: {str(e)}")
            
    def send_message(self):
        try:
            message_input = self.root.get_screen('chat').ids.message_input
            message = message_input.text.strip()

            if message:
                # Send user message
                self.add_message_bubble(message, is_user=True)
                message_input.text = ""

                if together_client:
                    try:
                        def get_bot_response(dt):
                            try:
                                response = together_client.chat.completions.create(
                                    model="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
                                    messages=[{"role": "user", "content": message}],
                                    max_tokens=512,
                                    temperature=0.7,
                                    top_p=0.7,
                                    top_k=50,
                                    repetition_penalty=1,
                                    stop=["<|eot_id|>"],
                                )
                                ai_response = response.choices[0].message.content
                                self.add_message_bubble(ai_response, is_user=False)
                            except Exception as e:
                                self.add_message_bubble(f"Error: {str(e)}", is_user=False)

                        # 1.5 second delay for bot response
                        Clock.schedule_once(get_bot_response, 1.5)
                        
                    except Exception as e:
                        Clock.schedule_once(lambda dt: self.add_message_bubble(f"Error: {str(e)}", is_user=False), 1.5)
                else:
                    Clock.schedule_once(lambda dt: self.add_message_bubble("Sorry, chat functionality is currently unavailable.", is_user=False), 1.5)
            else:
                self.show_error_dialog("Error", "Please enter a message.")
        except Exception as e:
            self.show_error_dialog("Error", f"Send message error: {str(e)}")
            
    def mic_function(self):
        try:
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                self.add_message_bubble("Listening for your message...", is_user=False)
                
                try:
                    recognizer.adjust_for_ambient_noise(source)
                    audio = recognizer.listen(source)
                    speech_text = recognizer.recognize_google(audio)
                    
                    self.add_message_bubble(speech_text, is_user=True)
                    
                    if together_client:
                        try:
                            response = together_client.chat.completions.create(
                                model="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
                                messages=[{"role": "user", "content": speech_text}],
                                max_tokens=512,
                                temperature=0.7,
                                top_p=0.7,
                                top_k=50,
                                repetition_penalty=1,
                                stop=["<|eot_id|>"],
                            )
                            ai_response = response.choices[0].message.content
                            self.add_message_bubble(ai_response, is_user=False)
                        except Exception as e:
                            self.add_message_bubble(f"Error getting AI response: {str(e)}", is_user=False)
                    else:
                        self.add_message_bubble("Sorry, chat functionality is currently unavailable.", is_user=False)

                except sr.UnknownValueError:
                    self.add_message_bubble("Could not understand the audio.", is_user=False)
                except sr.RequestError as e:
                    self.add_message_bubble(f"Error with speech recognition service: {e}", is_user=False)

        except Exception as e:
            self.show_error_dialog("Error", f"Microphone error: {str(e)}")

    def save_chat(self):
        try:
            chat_messages = []
            chat_list = self.root.get_screen('chat').ids.chat_list
            for child in chat_list.children:
                if isinstance(child, ChatBubble):
                    chat_messages.append(f"{'You' if child.is_user else 'AI'}: {child.message}")
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chat_{timestamp}.txt"
            filepath = os.path.join(os.getcwd(), filename)
            
            with open(filepath, 'w') as f:
                f.write('\n'.join(chat_messages))
            self.show_error_dialog("Success", f"Chat saved to {filename}.")
        except Exception as e:
            self.show_error_dialog("Error", f"Failed to save chat: {e}")

# Flask routes
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400

        if together_client:
            try:
                response = together_client.chat.completions.create(
                    model="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
                    messages=[{"role": "user", "content": message}],
                    max_tokens=512,
                    temperature=0.7,
                    top_p=0.7,
                    top_k=50,
                    repetition_penalty=1,
                    stop=["<|eot_id|>"],
                )
                return jsonify({'response': response.choices[0].message.content})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        else:
            return jsonify({'error': 'Chat functionality unavailable'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

KV = '''
ScreenManager:
    SplashPage:
    LoginPage:
    SignupPage:
    ChatPage:

<SplashPage>:
    name: "splash"
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: app.theme_cls.primary_color
        padding: dp(20)
        
        MDBoxLayout:
            orientation: "vertical"
            spacing: dp(20)
            size_hint: None, None
            size: dp(300), dp(400)
            pos_hint: {"center_x": .5, "center_y": .5}
            md_bg_color: 1, 1, 1, 1
            radius: [20]
            padding: dp(20)
            
            MDLabel:
                text: "SmartChat"
                font_style: "H3"
                halign: "center"
                theme_text_color: "Primary"
            
            MDLabel:
                text: "Welcome to SmartChat"
                font_style: "Subtitle1"
                halign: "center"
                theme_text_color: "Secondary"
                
            MDLabel:
                text: "Your AI Assistant"
                halign: "center"
                theme_text_color: "Secondary"
            
            Widget:
                size_hint_y: None
                height: dp(20)
            
            MDRaisedButton:
                text: "Get Started"
                size_hint_x: 0.8
                height: dp(50)
                pos_hint: {"center_x": .5}
                md_bg_color: app.theme_cls.primary_color
                on_release: root.manager.current = 'main'

<LoginPage>:
    name: "main"
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: app.theme_cls.primary_color
        
        MDCard:
            orientation: "vertical"
            size_hint: None, None
            size: dp(320), dp(450)
            pos_hint: {"center_x": .5, "center_y": .5}
            padding: dp(20)
            spacing: dp(20)
            elevation: 3
            radius: [20]
            
            MDLabel:
                text: "Welcome Back"
                font_style: "H4"
                halign: "center"
                adaptive_height: True
                
            MDLabel:
                text: "Login to continue"
                theme_text_color: "Secondary"
                halign: "center"
                adaptive_height: True
            
            Widget:
                size_hint_y: None
                height: dp(20)
            
            MDTextField:
                id: email
                hint_text: "Email"
                icon_left: "email"
                mode: "round"
                size_hint_x: None
                width: dp(280)
                pos_hint: {"center_x": .5}
            
            MDTextField:
                id: password
                hint_text: "Password"
                icon_left: "lock"
                mode: "round"
                password: True
                size_hint_x: None
                width: dp(280)
                pos_hint: {"center_x": .5}
            
            MDRaisedButton:
                text: "LOGIN"
                size_hint_x: 1
                height: dp(50)
                md_bg_color: app.theme_cls.primary_color
                on_release: app.login()
            
            MDTextButton:
                text: "Don't have an account? Sign Up"
                theme_text_color: "Primary"
                pos_hint: {"center_x": .5}
                on_release: root.manager.current = "signup"
<SignupPage>:
    name: "signup"
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: app.theme_cls.primary_color
        
        MDTopAppBar:
            title: "Create Account"
            left_action_items: [["arrow-left", lambda x: setattr(root.manager, 'current', 'main')]]
            elevation: 2
        
        MDCard:
            orientation: "vertical"
            size_hint: None, None
            size: dp(320), dp(500)
            pos_hint: {"center_x": .5, "center_y": .5}
            padding: dp(20)
            spacing: dp(20)
            elevation: 3
            radius: [20]
            
            MDLabel:
                text: "Create Account"
                font_style: "H4"
                halign: "center"
                adaptive_height: True
            
            MDTextField:
                id: name
                hint_text: "Full Name"
                icon_left: "account"
                mode: "round"
                size_hint_x: None
                width: dp(280)
                pos_hint: {"center_x": .5}
            
            MDTextField:
                id: email
                hint_text: "Email"
                icon_left: "email"
                mode: "round"
                size_hint_x: None
                width: dp(280)
                pos_hint: {"center_x": .5}
            
            MDTextField:
                id: password
                hint_text: "Password"
                icon_left: "lock"
                mode: "round"
                password: True
                size_hint_x: None
                width: dp(280)
                pos_hint: {"center_x": .5}
            
            MDTextField:
                id: confirm_password
                hint_text: "Confirm Password"
                icon_left: "lock-check"
                mode: "round"
                password: True
                size_hint_x: None
                width: dp(280)
                pos_hint: {"center_x": .5}
            
            MDRaisedButton:
                text: "SIGN UP"
                size_hint_x: 1
                height: dp(50)
                md_bg_color: app.theme_cls.primary_color
                on_release: app.signup()
<ChatPage>:
    name: "chat"
    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            title: "ChatBot"
            left_action_items: [["menu", lambda x: app.open_sidebar()]]
            right_action_items: [["theme-light-dark", lambda x: app.toggle_theme()], ["cog", lambda x: app.open_settings()]]
            elevation: 2

        # Chat Area with FlexibleListLayout
        MDBoxLayout:
            orientation: "vertical"
            padding: dp(10)
            spacing: dp(10)
            md_bg_color: app.theme_cls.bg_normal
            
            ScrollView:
                id: chat_scroll
                do_scroll_x: False
                
                MDGridLayout:
                    id: chat_list
                    cols: 1
                    spacing: dp(10)
                    padding: dp(10), dp(10)
                    size_hint_y: None
                    height: self.minimum_height
                    adaptive_height: True
            
            # Message Input Area
            MDCard:
                size_hint_y: None
                height: dp(60)
                padding: dp(5)
                spacing: dp(5)
                radius: [30]
                md_bg_color: app.theme_cls.bg_dark
                
                MDTextField:
                    id: message_input
                    hint_text: "Type your message..."
                    mode: "round"
                    multiline: False
                    size_hint: 1, None
                    height: dp(40)
                
                MDIconButton:
                    icon: "microphone"
                    theme_text_color: "Custom"
                    text_color: app.theme_cls.primary_color
                    on_release: app.mic_function()
                
                MDIconButton:
                    icon: "send"
                    theme_text_color: "Custom"
                    text_color: app.theme_cls.primary_color
                    on_release: app.send_message()

<ChatBubble>:
    size_hint_x: 0.7
    adaptive_height: True
    padding: dp(12)
    spacing: dp(5)
    radius: [20]
    elevation: 0
    orientation: 'vertical'
    
    canvas.before:
        Color:
            rgba: [0.6, 0.2, 0.8, 1] if self.is_user else [0.9, 0.9, 0.9, 1]
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [20]
    
    MDBoxLayout:
        orientation: 'horizontal'
        adaptive_height: True
        spacing: 0
        padding: 0
        
        MDLabel:
            text: root.message
            theme_text_color: "Custom"
            text_color: [1, 1, 1, 1] if root.is_user else [0, 0, 0, 1]
            adaptive_height: True
            size_hint_x: 1
            text_size: self.width, None
            halign: 'left'
            valign: 'middle'
            padding: dp(8), dp(4)

<SideBar>:
    id: sidebar
    radius: (0, 16, 16, 0)
    
    MDBoxLayout:
        orientation: "vertical"
        padding: dp(10)
        spacing: dp(10)
        
        MDLabel:
            text: "Settings"
            font_style: "H6"
            adaptive_height: True
            padding: dp(10)
        
        MDList:
            OneLineIconListItem:
                text: "Save Chat"
                on_release: app.save_chat()
                IconLeftWidget:
                    icon: "content-save"
            
            OneLineIconListItem:
                text: "Toggle Theme"
                on_release: app.toggle_theme()
                IconLeftWidget:
                    icon: "theme-light-dark"
            
            OneLineIconListItem:
                text: "Logout"
                on_release: 
                    app.root.current = "main"
                    root.set_state("close")
                IconLeftWidget:
                    icon: "logout"
'''

def run_app():
    try:
        from threading import Thread
        
        flask_thread = Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False))
        flask_thread.daemon = True
        flask_thread.start()
        
        ChatApp().run()
    except Exception as e:
        print(f"Error running app: {str(e)}")

if __name__ == "__main__":
    run_app()