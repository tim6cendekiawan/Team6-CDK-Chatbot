from openai import OpenAI
import tiktoken
import requests
import os
import streamlit as st
from icalendar import Calendar
from datetime import datetime
import pytz


# Constants
DEFAULT_API_KEY = "be06563022d9991254cfb79daac5c38fe19d3e0f9f1ef5d3d45b968a3ef85324"
DEFAULT_BASE_URL = "https://api.together.xyz/v1"
DEFAULT_MODEL = "meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo"
DEFAULT_TEMPERATURE = 0.6
DEFAULT_MAX_TOKENS = 1096
DEFAULT_TOKEN_BUDGET = 4096


# ConversationManager class to handle AI conversation
class ConversationManager:
    def __init__(self, api_key=None, base_url=None, model=None, temperature=None, max_tokens=None, token_budget=None):
        self.api_key = api_key or DEFAULT_API_KEY
        self.base_url = base_url or DEFAULT_BASE_URL
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

        self.model = model or DEFAULT_MODEL
        self.temperature = temperature or DEFAULT_TEMPERATURE
        self.max_tokens = max_tokens or DEFAULT_MAX_TOKENS
        self.token_budget = token_budget or DEFAULT_TOKEN_BUDGET

        self.system_message = "You are a friendly and supportive assistant. You answer with kindness and patience."
        self.conversation_history = [{"role": "system", "content": self.system_message}]

    # Function to count tokens in a given text
    def count_tokens(self, text):
        try:
            encoding = tiktoken.encoding_for_model(self.model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        tokens = encoding.encode(text)
        return len(tokens)

    # Function to calculate the total tokens used in the conversation
    def total_tokens_used(self):
        try:
            return sum(self.count_tokens(message['content']) for message in self.conversation_history)
        except Exception as e:
            print(f"Error calculating total tokens: {e}")
            return None

    # Function to ensure the token usage does not exceed the budget
    def enforce_token_budget(self):
        try:
            while self.total_tokens_used() > self.token_budget:
                if len(self.conversation_history) <= 1:
                    break
                self.conversation_history.pop(1)
        except Exception as e:
            print(f"Error enforcing token budget: {e}")

    # Function to get AI response based on user input
    def chat_completion(self, prompt, temperature=None, max_tokens=None, model=None):
        temperature = temperature or self.temperature
        max_tokens = max_tokens or self.max_tokens
        model = model or self.model

        self.conversation_history.append({"role": "user", "content": prompt})
        self.enforce_token_budget()

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=self.conversation_history,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            print(f"Error generating response: {e}")
            return None

        ai_response = response.choices[0].message.content
        self.conversation_history.append({"role": "assistant", "content": ai_response})

        return ai_response

    # Function to reset the conversation history
    def reset_conversation_history(self):
        self.conversation_history = [{"role": "system", "content": self.system_message}]


# CalendarManager class to handle calendar functionality
class CalendarManager:
    def __init__(self):
        self.events = []

    # Function to parse an ICS file and extract calendar events
    def parse_ics_file(self, ics_content):
        try:
            cal = Calendar.from_ical(ics_content)
            self.events = [
                {
                    'summary': str(component.get('summary', 'No Title')),
                    'start': component.get('dtstart').dt,
                    'end': component.get('dtend').dt if component.get('dtend') else None,
                    'description': str(component.get('description', '')),
                    'location': str(component.get('location', ''))
                }
                for component in cal.walk() if component.name == "VEVENT"
            ]
            return True
        except Exception as e:
            print(f"Error parsing ICS file: {e}")
            return False


# Function to add calendar upload section in Streamlit sidebar
def add_calendar_upload():
    st.sidebar.write("Calendar Import")
    uploaded_file = st.sidebar.file_uploader("Upload ICS File", type=['ics'])

    if uploaded_file:
        calendar_manager = CalendarManager()
        ics_content = uploaded_file.read()

        if calendar_manager.parse_ics_file(ics_content):
            st.sidebar.success("Calendar successfully imported!")
            st.write("### Imported Calendar Events")
            for event in calendar_manager.events:
                with st.expander(f"📅 {event['summary']}"):
                    st.write(f"**Start:** {event['start'].strftime('%Y-%m-%d %H:%M')}")
                    if event['end']:
                        st.write(f"**End:** {event['end'].strftime('%Y-%m-%d %H:%M')}")
                    if event['location']:
                        st.write(f"**Location:** {event['location']}")
                    if event['description']:
                        st.write(f"**Description:** {event['description']}")
        else:
            st.sidebar.error("Error importing calendar file")


# Function to retrieve EC2 instance ID
def get_instance_id():
    try:
        token = requests.put(
            "http://169.254.169.254/latest/api/token",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
            timeout=1
        ).text

        instance_id = requests.get(
            "http://169.254.169.254/latest/meta-data/instance-id",
            headers={"X-aws-ec2-metadata-token": token},
            timeout=1
        ).text
        return instance_id
    except requests.exceptions.RequestException:
        return "Instance ID not available (local or retrieval error)"


# Main Streamlit application
st.title("AI Chatbot")

# Display EC2 Instance ID
instance_id = get_instance_id()
st.write(f"**EC2 Instance ID**: {instance_id}")

# Initialize ConversationManager object
if 'chat_manager' not in st.session_state:
    st.session_state['chat_manager'] = ConversationManager()

chat_manager = st.session_state['chat_manager']

# User input for chat
user_input = st.chat_input("Write a message")

# Calendar upload section
add_calendar_upload()

# Get AI response based on user input
if user_input:
    response = chat_manager.chat_completion(user_input)

# Display conversation history
for message in chat_manager.conversation_history:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.write(message["content"])

# Sidebar options for chatbot settings
with st.sidebar:
    st.write("Settings")
    set_token = st.slider("Max Tokens per Message", 10, 1096, DEFAULT_MAX_TOKENS, step=1)
    st.session_state['chat_manager'].max_tokens = set_token

    #Customize the chatbot's personality
    set_custom_message = st.selectbox("System Message", ("Professional", "Friendly", "Humorous"))
    if set_custom_message == "Professional":
        custom_message = "You are a professional assistant. You provide accurate and reliable information, and you are always willing to answer questions and help the user achieve their goals."
    elif set_custom_message == "Friendly":
        custom_message = "You are a friendly and supportive guide. You answer questions with kindness, encouragement, and patience, always looking to help the user feel comfortable and confident."
    elif set_custom_message == "Humorous":
        custom_message = "You are a humorous companion, adding fun to the conversation."


    set_temp = st.slider("Temperature", 0.0, 1.0, DEFAULT_TEMPERATURE, step=0.1)
    st.session_state['chat_manager'].temperature = set_temp

    st.write("Reset Conversation")
    if st.button("Reset"):
        chat_manager.reset_conversation_history()
        st.rerun()
