from openai import OpenAI
import tiktoken
import requests
from dotenv import load_dotenv
import os
import streamlit as st
from icalendar import Calendar
from datetime import datetime
import pytz
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np



# Muat file .env
load_dotenv()

# Ambil nilai dari variabel lingkungan yang telah disimpan di .env
DEFAULT_API_KEY = os.getenv("DEFAULT_API_KEY")
DEFAULT_BASE_URL = os.getenv("DEFAULT_BASE_URL")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL")
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", 0.6))
DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", 1096))
DEFAULT_TOKEN_BUDGET = int(os.getenv("DEFAULT_TOKEN_BUDGET", 4096))

st.set_page_config(
    page_title="ARIA Chatbot",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded",
)
st.image("assets/ariaa.png")
st.markdown(
    """
    <p style='font-size: 18px; text-align: center;'>
        Assistant for Reminders, Information, and Agendas
    </p>
    """, unsafe_allow_html=True)

def convert_to_wib(utc_time):
    wib_zone = pytz.timezone('Asia/Jakarta')
    if isinstance(utc_time, datetime):
        return utc_time.astimezone(wib_zone)
    return None

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

        self.system_message = ("You are a friendly and supportive daily planner assistant, your name is ARIA (Assistant for Reminders, Information, and Agendas) and you generate a scheduke in GMT 07 OR indonesian hours only. You answer with kindness and patience. and breakdown to point point"
                                "You are a helpful assistant named ARIA. "
                                "You help with scheduling but always ask the user before adding or modifying their schedule. "
                                "You generate suggestions with kindness and patience."
                                "You have access to the user's imported calendar data. Use this information to help with scheduling and recommendations.")
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

    # Tambahkan flag untuk melacak apakah rekomendasi sudah diberikan
    if "recommendation_added" not in st.session_state:
        st.session_state["recommendation_added"] = False


    # Function to get AI response based on user input
    def chat_completion(self, prompt, temperature=None, max_tokens=None, model=None):

        calendar_data = st.session_state.get("calendar_data", None)

        # Only add calendar to prompt if it exists and not previously added
        recommendation_prompt = ""
        if calendar_data and not st.session_state.get("recommendation_added", False):
            activity_df, recommendation = analyze_activity_schedule(calendar_data)
            calendar_info = "\n".join(
                [f"Event: {event['summary']} | Start: {convert_to_wib(event['start']).strftime('%Y-%m-%d %H:%M')} | End: {convert_to_wib(event['end']).strftime('%Y-%m-%d %H:%M') if event['end'] else 'No End Time'}"
                for event in calendar_data]
            )
            # Add calendar prompt as "system" message
            self.conversation_history.insert(0, {
                "role": "system",
                "content": f"Here are some calendar events:\n{calendar_info}"
            })
            st.session_state["recommendation_added"] = True # Mark calendar as used
        
        prompt += recommendation_prompt  # Menambahkan prompt ke input pengguna
        
        self.conversation_history.append({"role": "user", "content": prompt})
        self.enforce_token_budget()
        
        # Menggunakan parameter lain untuk mengatur respons AI
        temperature = temperature or self.temperature
        max_tokens = max_tokens or self.max_tokens
        model = model or self.model

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
        self.ai_response = ai_response
        self.conversation_history.append({"role": "assistant", "content": ai_response})

        return ai_response



    # Function to reset the conversation history
    def reset_conversation_history(self):
        self.conversation_history = [{"role": "system", "content": self.system_message}]

    
#---------------------calender-------------------------------+
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

    def convert_to_wib(self, utc_time):
        # Western Indonesia Time Zone (WIB)
        wib_zone = pytz.timezone('Asia/Jakarta')
        
        # Make sure the UTC time received is datetime
        if isinstance(utc_time, datetime):
            # Convert UTC time to WIB
            wib_time = utc_time.astimezone(wib_zone)
            return wib_time
        return None
 
st.markdown("""
    <style>
    /* Ubah tampilan file uploader */
    .stFileUploader label {
        font-weight: bold;
        color: #6b705c;
        font-size: 16px;
    }
    .stFileUploader div[data-testid="stFileUploadDropzone"] {
        border: 2px dashed #d3c0a7;
        border-radius: 10px;
        padding: 15px;
        background-color: #fefae0;
        text-align: center;
    }
    .stFileUploader div[data-testid="stFileUploadDropzone"]:hover {
        background-color: #f5e8c7;
    }
    .stFileUploader button {
        background-color: #d3c0a7;
        color: black;
        border: none;
        border-radius: 5px;
        padding: 5px 10px;
    }
    .stFileUploader button:hover {
        background-color: #b7a38b;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)        
 
        
# Function to add calendar upload (outside Calendar Manager class)
def add_calendar_upload():
    st.sidebar.markdown("""
        <div style="font-weight: 600; font-size: 16px;">
            Calendar Import
        </div>
    """, unsafe_allow_html=True)
    uploaded_file = st.sidebar.file_uploader("Upload Your ICS File", type=['ics'])

    if uploaded_file:
        calendar_manager = CalendarManager()
        ics_content = uploaded_file.read()

        if calendar_manager.parse_ics_file(ics_content):
            st.sidebar.success("Calendar successfully imported!")
            st.session_state["calendar_added"] = False  # Reset calendar processing state
            st.session_state["calendar_data"] = calendar_manager.events
            st.session_state["schedule"] = calendar_manager.events  # Tambahkan ini
            st.session_state["calendar_prompt_added"] = False  # Reset flag for prompt addition
        else:
            st.sidebar.error("Error importing calendar file")

#---------------------calender-------------------------------+



#---------------------anlyzing-------------------------------+

# Fungsi untuk menganalisis waktu yang dihabiskan pada jenis kegiatan
def analyze_activity_schedule(calendar_data):
    activities = []
    work_time = 0
    workout_time = 0
    rest_time = 0

    # Proses data kalender untuk menganalisis kegiatan
    for event in calendar_data:
        event_duration = (event['end'] - event['start']).total_seconds() / 3600  # dalam jam
        if 'work' in event['summary'].lower():
            work_time += event_duration
        elif 'workout' in event['summary'].lower():
            workout_time += event_duration
        else:
            rest_time += event_duration
        activities.append({'Event': event['summary'], 'Duration (hours)': event_duration})

    # Menyusun data ke dalam DataFrame
    activity_df = pd.DataFrame(activities)
    
    # Analisis: Jika waktu kerja lebih banyak daripada olahraga
    if work_time > workout_time:
        recommendation = "You seem to be working a lot! Consider taking a break or doing some physical activities."
    elif workout_time > work_time:
        recommendation = "Great job on staying active! Keep it up."
    else:
        recommendation = "Balance is good, but consider increasing your physical activity."

    return activity_df, recommendation

def plot_activity_analysis(activity_df):
    activity_summary = activity_df.groupby('Event')['Duration (hours)'].sum().sort_values(ascending=False)
    
    plt.figure(figsize=(10,6))
    activity_summary.plot(kind='bar', color=['#FF6347', '#4682B4', '#32CD32'])
    plt.title('Activity Analysis')
    plt.xlabel('Activity Type')
    plt.ylabel('Total Duration (hours)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(plt)

def analyze_and_visualize_schedule():
    if "schedule" not in st.session_state or not st.session_state["schedule"]:
        st.write("No schedule data to analyze.")
        return

    schedule_data = st.session_state["schedule"]
    activity_df, recommendation = analyze_activity_schedule(schedule_data)
    st.session_state["recommendation"] = recommendation  # Simpan rekomendasi

    # # Tampilkan rekomendasi
    # st.write("### Schedule Analysis")
    # st.write(recommendation)

    # Plot analisis
    # plot_activity_analysis(activity_df)

if "schedule" in st.session_state:
    analyze_and_visualize_schedule()

#---------------------anlyzing-------------------------------+


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

# Initialize ConversationManager object
if 'chat_manager' not in st.session_state:
    st.session_state['chat_manager'] = ConversationManager()

chat_manager = st.session_state['chat_manager']

# User input for chat
st.markdown("""
    <style>
    /* placeholder text input */
    .stChatInput textarea::placeholder {
        color: black;
    }

    /* button send text input */
    .stChatInput button {
        color: black !important;
        cursor: pointer;
    }

    </style>
    """, unsafe_allow_html=True)
user_input = st.chat_input("Write a message")

# Calendar upload section
# add_calendar_upload()



# Get AI response based on user input
if user_input:
    response = chat_manager.chat_completion(user_input)

    # Cek apakah respons sudah mencakup rekomendasi atau jadwal
    if "Would you like me to suggest some improvements" in chat_manager.ai_response:
        # Menyediakan rekomendasi jadwal jika diperlukan
        recommendation = st.session_state.get("recommendation", "No recommendation available.")
        if user_input.lower() in ["yes", "sure", "okay"]:
            st.write("Here are the suggested improvements:")
            st.write(recommendation)

            # Menambahkan ke jadwal jika disetujui
            new_event = {"summary": "Suggested Improvement", "start": datetime.now(), "end": datetime.now() + timedelta(hours=1)}
            st.session_state["schedule"].append(new_event)

            # Re-analyze schedule
            analyze_and_visualize_schedule()

        elif user_input.lower() in ["no", "not now"]:
            st.write("Got it! Let me know if you need help later.")
    
    # Menangani permintaan untuk jadwal hanya sekali
    elif "jadwal saya" in user_input.lower():
        schedule = st.session_state.get("schedule", None)
        if schedule:
            # Formatkan jadwal untuk ditampilkan
            formatted_schedule = "\n".join(
                f"{convert_to_wib(event['start']).strftime('%H:%M')} - {convert_to_wib(event['end']).strftime('%H:%M')} : {event['summary']}" 
                for event in schedule
            )
            # response = f"Berikut adalah jadwal Anda:\n{formatted_schedule}"
        else:
            response = "Saya tidak menemukan data jadwal. Silakan unggah kalender Anda terlebih dahulu."

        # # Tambahkan ke riwayat percakapan hanya jika belum ada respons yang duplikat
        # chat_manager.conversation_history.append({"role": "assistant", "content": response})
        # st.chat_message("assistant").markdown(response)

st.markdown("""
                <style>
                .stChatMessage {
                   background-color: transparent;
                }
                </style>
            """, unsafe_allow_html=True)

# Display conversation history
for message in chat_manager.conversation_history:
    if message["role"] != "system":  # Ignore system messages
        if message["role"] == "user":
            with st.chat_message("user"):
                st.markdown(
                    f"""
                    <div style="background-color: #dbc6a7; border-radius: 10px; padding: 10px;">
                        <p style='color: black'>{message['content']}</p>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
        elif message["role"] == "assistant":
            with st.chat_message("assistant"):
                st.markdown(
                    f"""
                    <div style="background-color:  #b19a70; border-radius: 10px; padding: 10px;">
                        <p style='color: black'>{message['content']}</p>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )


# Sidebar options for chatbot settings
with st.sidebar:
    selected = option_menu(
        menu_title=None,
        options=["Import Calendar", "My Calendar", "Settings"],  # Menambahkan "Settings" dalam tanda kutip
        icons=["cloud-arrow-up", "calendar", "gear"],  # Ikon untuk masing-masing menu
        default_index=0,styles={
            "container": {"padding": "5px", "background-color": "#fefae0"},
            "nav-link": {"font-size": "15px",  "text-align": "left", "margin": "0px"},
            "nav-link-selected": {"background-color": "#d3c0a7", "font-weight": "500","color": "white"},
        }
    )

    # Menu untuk Import (Upload ICS File)
    if selected == "Import Calendar":
        add_calendar_upload()

    # Menu untuk Calendar (Menampilkan Kalender dan Acara yang Diimpor)
    if selected == "My Calendar":
    # Check if calendar data exists in session state
        if "calendar_data" in st.session_state and st.session_state["calendar_data"]:
            st.markdown("""
                <style>
                .custom-title {
                    font-size: 16px;
                    font-weight: 600;
                    color: black; 
                    margin-bottom: 5px;
                }
                </style>
                <div class="custom-title">Imported Calendar Events</div>
            """, unsafe_allow_html=True)
            
            # Loop through the events and display them in the main area
            for event in st.session_state["calendar_data"]:
                start_time_wib = convert_to_wib(event['start'])
                end_time_wib = convert_to_wib(event['end']) if event['end'] else None
                # st.markdown("""
                #     <style>
                #     .stExpander {
                #         border: 1px solid #d3c0a7; /* Border ringan */
                #         background-color: #fefae0; /* Warna latar belakang */
                #         border-radius: 8px; /* Membuat sudut rounded */
                #         transition: background-color 0.3s ease; /* Animasi transisi */
                #     }
                #     .stExpander:hover {
                #         background-color: #b7a38b; /* Warna lebih gelap saat hover */
                #     }
                #     /* Teks di dalam expander */
                #     .stExpander .stMarkdown {
                #         color: black; /* Warna teks */
                #     }
                #     </style>
                # """, unsafe_allow_html=True)
            # Using expander to display the details of each event
                with st.expander(f"📅 **{event['summary']}**"):
                    if start_time_wib:
                        st.write(f"**Start:** {start_time_wib.strftime('%Y-%m-%d %H:%M')}")
                    else:
                        st.write("**Start:** No start time")
                    
                    if end_time_wib:
                        st.write(f"**End:** {end_time_wib.strftime('%Y-%m-%d %H:%M')}")
                    else:
                        st.write("**End:** No end time")
                    
                    if event.get('location'):
                        st.write(f"**Location:** {event['location']}")
                    if event.get('description'):
                        st.write(f"**Description:** {event['description']}")
        else:
            st.error("No calendar events found. Please upload a calendar file.")

    # Menu untuk Settings
    elif selected == "Settings":        
        # Pengaturan Max Tokens dan Temperature
        st.sidebar.markdown("""
            <div style="font-weight: 600; font-size: 16px;">
                Settings
            </div>
        """, unsafe_allow_html=True)
        
        # Slider untuk Max Tokens per Message
        set_token = st.slider("Max Tokens per Message", 10, 1096, DEFAULT_MAX_TOKENS, step=1)
        st.session_state['chat_manager'].max_tokens = set_token

        # Slider untuk Temperature
        set_temp = st.slider("Temperature", 0.0, 1.0, DEFAULT_TEMPERATURE, step=0.1)
        st.session_state['chat_manager'].temperature = set_temp

        # Tampilkan EC2 Instance ID
        instance_id = get_instance_id()
        st.sidebar.markdown(
            f"""
            <div style=" margin-top: 20px; width: 100%; text-align: center; font-weight: 600">
                EC2 Instance ID: {instance_id}
            </div>
            """, 
            unsafe_allow_html=True
        )
    st.markdown("""
        <style>
        .stSidebar Button {
            background-color: #fefae0;
            color: black;
            border: none;
            border-radius: 5px;
            padding: 5px 10px;
            display: block;
            width: 100%;
        }
        .stSidebar Button:hover {
            background-color: #e4d7b6;
            color: black;
        }

        .stSidebar write{
            color: black !important;
        }
        </style>
    """, unsafe_allow_html=True)

    if st.sidebar.button("Reset Conversation"):
        st.sidebar.write("Conversation reset!")
        chat_manager.reset_conversation_history()
        st.rerun() 