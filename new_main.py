import sqlite3
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.core.window import Window
from twilio.rest import Client
import geocoder

# Database Setup
DB_NAME = 'clariyo.db'

def create_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        email TEXT,
                        password TEXT,
                        medical_condition TEXT,
                        guardian_name TEXT,
                        guardian_contact TEXT
                    )''')
    conn.commit()
    conn.close()

create_db()

# Twilio Configuration
TWILIO_SID = <your twilio account SID>
TWILIO_AUTH_TOKEN = <your twilio account auth token>
TWILIO_PHONE_NUMBER = <your twilio account phone_number>

class SignUpScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.name_input = TextInput(hint_text="Enter Name")
        self.email_input = TextInput(hint_text="Enter Email")
        self.password_input = TextInput(hint_text="Enter Password", password=True)
        self.condition_input = TextInput(hint_text="Medical Condition")
        self.guardian_name_input = TextInput(hint_text="Guardian Name")
        self.guardian_contact_input = TextInput(hint_text="Guardian Contact (Phone Number)")

        layout.add_widget(Label(text="Sign Up"))
        layout.add_widget(self.name_input)
        layout.add_widget(self.email_input)
        layout.add_widget(self.password_input)
        layout.add_widget(self.condition_input)
        layout.add_widget(self.guardian_name_input)
        layout.add_widget(self.guardian_contact_input)

        sign_up_btn = Button(text="Sign Up")
        sign_up_btn.bind(on_press=self.sign_up)
        layout.add_widget(sign_up_btn)

        self.add_widget(layout)

    def sign_up(self, instance):
        name = self.name_input.text
        email = self.email_input.text
        password = self.password_input.text
        condition = self.condition_input.text
        guardian_name = self.guardian_name_input.text
        guardian_contact = self.guardian_contact_input.text

        if not all([name, email, password, condition, guardian_name, guardian_contact]):
            self.show_popup("Error", "All fields are required!")
            return

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email, password, medical_condition, guardian_name, guardian_contact) VALUES (?, ?, ?, ?, ?, ?)", 
                       (name, email, password, condition, guardian_name, guardian_contact))
        conn.commit()
        conn.close()

        self.manager.current = 'profile'

    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.8, 0.5))
        popup.open()

class ProfileScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.user = None
        self.populate_profile()
        self.add_widget(self.layout)

        # Bind Ctrl + P for triggering alert
        Window.bind(on_key_down=self.on_key_down)

    def populate_profile(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY id DESC LIMIT 1")
        self.user = cursor.fetchone()
        conn.close()

        self.layout.clear_widgets()
        if self.user:
            self.layout.add_widget(Label(text=f"Name: {self.user[1]}"))
            self.layout.add_widget(Label(text=f"Medical Condition: {self.user[4]}"))
            self.layout.add_widget(Label(text=f"Guardian: {self.user[5]}"))
        else:
            self.layout.add_widget(Label(text="No user data available."))

        trigger_btn = Button(text="Trigger Alert")
        trigger_btn.bind(on_press=self.trigger_alert)
        self.layout.add_widget(trigger_btn)

    def on_key_down(self, window, key, *args):
        if key == 112:  # Key code for 'P'
            if Window.modifiers and 'ctrl' in Window.modifiers:
                self.trigger_alert(None)

    def trigger_alert(self, instance):
        if self.user:
            guardian_contact = self.user[6]
            guardian_name = self.user[5]

            # Fetch location
            location = geocoder.ip('me')
            location_msg = f"Location: {location.latlng}" if location.latlng else "Location: Unknown"

            # Sending an SMS as an alert
            try:
                client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
                message = f"{self.user[1]} needs immediate assistance.\nContact them at {guardian_contact}.\n{location_msg}"
                client.messages.create(
                    body=message,
                    from_=TWILIO_PHONE_NUMBER,
                    to=guardian_contact
                )
                self.show_popup("Success", f"Alert sent to {guardian_name}!")
            except Exception as e:
                self.show_popup("Error", f"Failed to send alert: {e}")

    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.8, 0.5))
        popup.open()

class ClariyoApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(SignUpScreen(name='signup'))
        sm.add_widget(ProfileScreen(name='profile'))
        return sm

if __name__ == '__main__':
    ClariyoApp().run()