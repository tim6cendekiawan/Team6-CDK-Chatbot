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
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 512
DEFAULT_TOKEN_BUDGET = 4096


# ConversationManager Class
class ConversationManager:
    def __init__(self, api_key=None, base_url=None, model=None, temperature=None, max_tokens=None, token_budget=None):
        self.api_key = api_key or DEFAULT_API_KEY
        self.base_url = base_url or DEFAULT_BASE_URL
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

        self.model = model or DEFAULT_MODEL
        self.temperature = temperature or DEFAULT_TEMPERATURE
        self.max_tokens = max_tokens or DEFAULT_MAX_TOKENS
        self.token_budget = token_budget or DEFAULT_TOKEN_BUDGET

        self.system_message = "You are a friendly and supportive guide. You answer questions with kindness, encouragement, and patience, always looking to help the user feel comfortable and confident."
        self.conversation_history = [{"role": "system", "content": self.system_message}]

    def count_tokens(self, text):
        try:
            encoding = tiktoken.encoding_for_model(self.model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        tokens = encoding.encode(text)
        return len(tokens)

    def total_tokens_used(self):
        try:
            return sum(self.count_tokens(message['content']) for message in self.conversation_history)
        except Exception as e:
            print(f"Error calculating total tokens used: {e}")
            return None

    def enforce_token_budget(self):
        try:
            while self.total_tokens_used() > self.token_budget:
                if len(self.conversation_history) <= 1:
                    break
                self.conversation_history.pop(1)
        except Exception as e:
            print(f"Error enforcing token budget: {e}")

    def chat_completion(self, prompt, temperature=None, max_tokens=None, model=None):
        # Tambahkan logika agar prompt hanya muncul sekali
        if 'calendar_imported' in st.session_state and st.session_state['calendar_imported']:
            if not st.session_state.get('calendar_prompt_shown', False):
                prompt = "I have successfully imported your calendar. " + prompt  # Tambahkan konteks hanya sekali
                st.session_state['calendar_prompt_shown'] = True  # Tandai prompt sudah ditampilkan


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

    def reset_conversation_history(self):
        self.conversation_history = [{"role": "system", "content": self.system_message}]


# CalendarManager Class
class CalendarManager:
    def __init__(self):
        self.events = []

    def parse_ics_file(self, ics_content):
        try:
            cal = Calendar.from_ical(ics_content)
            parsed_events = []

            for component in cal.walk():
                if component.name == "VEVENT":
                    event = {
                        'summary': str(component.get('summary', 'No Title')),
                        'start': component.get('dtstart').dt,
                        'end': component.get('dtend').dt if component.get('dtend') else None,
                        'description': str(component.get('description', '')),
                        'location': str(component.get('location', ''))
                    }
                    parsed_events.append(event)

            self.events = parsed_events
            return True
        except Exception as e:
            print(f"Error parsing ICS file: {e}")
            return False


# Streamlit UI
def add_calendar_upload():
    """Function to handle the calendar file upload in Streamlit sidebar."""
    st.sidebar.write("Calendar Import")
    uploaded_file = st.sidebar.file_uploader("Upload ICS File", type=['ics'])

    if uploaded_file is not None:
        calendar_manager = CalendarManager()
        ics_content = uploaded_file.read()

        if calendar_manager.parse_ics_file(ics_content):
            st.sidebar.success("Calendar imported successfully!")
            st.session_state['calendar_imported'] = True  # Set the flag

            # Display events
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


def get_instance_id():
    """Retrieve the EC2 instance ID from AWS metadata using IMDSv2."""
    try:
        # Step 1: Get the token
        token = requests.put(
            "http://169.254.169.254/latest/api/token",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
            timeout=1
        ).text

        # Step 2: Use the token to get the instance ID
        instance_id = requests.get(
            "http://169.254.169.254/latest/meta-data/instance-id",
            headers={"X-aws-ec2-metadata-token": token},
            timeout=1
        ).text
        return instance_id
    except requests.exceptions.RequestException:
        return "Instance ID not available (running locally or error in retrieval)"


### Streamlit main app ###
st.title("AI Chatbot")

# Display EC2 Instance ID
instance_id = get_instance_id()
st.write(f"**EC2 Instance ID**: {instance_id}")

# Initialize the ConversationManager object
if 'chat_manager' not in st.session_state:
    st.session_state['chat_manager'] = ConversationManager()

chat_manager = st.session_state['chat_manager']

if 'conversation_history' not in st.session_state:
    st.session_state['conversation_history'] = chat_manager.conversation_history

conversation_history = st.session_state['conversation_history']

# Chat input from the user
user_input = st.chat_input("Write a message")

# Add calendar upload section
st.write("---")  # Add a separator
add_calendar_upload()

# Call the chat manager to get a response from the AI
if user_input:
    response = chat_manager.chat_completion(user_input)

# Display the conversation history
for message in conversation_history:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.write(message["content"])

# Option Chatbot with Sidebar
with st.sidebar:
    
    st.write("Option")
    set_token = st.slider("Max Tokens Per Message", min_value=10, max_value=512, value=DEFAULT_MAX_TOKENS, step=1)
    st.session_state['chat_manager'].max_tokens = set_token
    
    set_temp = st.slider("Temperature", min_value=0.0, max_value=1.0, value=DEFAULT_TEMPERATURE, step=0.1)
    st.session_state['chat_manager'].temperature = set_temp

    set_custom_message = st.selectbox("System Message", ("Custom", "Professional", "Friendly", "Humorous"))
    if set_custom_message == "Custom":
        custom_message = st.text_area("Custom System Message", key="custom_message", value=chat_manager.system_message)
    elif set_custom_message == "Professional":
        custom_message = "You are a professional assistant. You provide accurate and reliable information, and you are always willing to answer questions and help the user achieve their goals."
    elif set_custom_message == "Friendly":
        custom_message = "You are a friendly and supportive guide. You answer questions with kindness, encouragement, and patience, always looking to help the user feel comfortable and confident."
    elif set_custom_message == "Humorous":
        custom_message = "You are a humorous companion, adding fun to the conversation."

    if st.button("Set Custom Message", on_click=lambda: setattr(chat_manager, "system_message", custom_message)):
        chat_manager.reset_conversation_history()
        st.session_state['conversation_history'] = chat_manager.conversation_history
        st.session_state['chat_manager'] = chat_manager
        st.rerun()

    if st.button("Reset Conversation"):
        chat_manager.reset_conversation_history()
        st.session_state['conversation_history'] = chat_manager.conversation_history
        st.rerun()

    st.write("Current max_tokens:", st.session_state['chat_manager'].max_tokens)
    st.write("Current temperature:", st.session_state['chat_manager'].temperature)
