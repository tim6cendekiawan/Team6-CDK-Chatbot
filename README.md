# ARIA (Assistant for Reminders, Information, and Agendas)

<img src="(https://raw.githubusercontent.com/team6cendekiawan/Team6-CDK-Chatbot/refs/heads/main/assets/Aria_chatbot.png)" />


## About
**ARIA** is a smart chatbot designed to assist users in organizing their daily schedules more easily and efficiently. This project is developed as part of the **MSIB program at RevoU** by **Team 6 Cendekiawan**. ARIA integrates modern technology to provide users with a practical and flexible experience.

## Features
- **Daily Schedule Management**: Helps users create and organize daily activities with a clear structure.
- **Time Recommendations**: Calculates activity durations to create more realistic schedules.
- **Import Calendar (.ICS)**: Allows users to upload calendar files to easily integrate schedules.
- **Simple Interface**: Designed for ease of use with intuitive navigation.

## Getting Started
### Prerequisites
Make sure you have the following:
- **Python** version 3.8 or newer
- Internet connection

### Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/tim6cendekiawan/Team6-CDK-Chatbot.git

2. Navigate to the project directory:
   ```bash
   cd Team6-CDK-Chatbot
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

#### Dependencies
This project uses the following libraries:
- `openai`
- `tiktoken`
- `requests`
- `python-dotenv`
- `streamlit`
- `icalendar`
- `pytz`
- `datetime`
- `streamlit-option-menu`
- `matplotlib`
- `pandas`
- `numpy`

4. Run the application :
   ```bash
   streamlit run main.py
   ```

## How to Use
1. Open the application in a browser: (localhost)
2. Use the interface to:
   - Add new schedules
   - Upload a calendar file (.ICS)
   - Get optimized schedule recommendations

### How to Export Calendar from Google to .ICS File

To import your Google Calendar into ARIA, you'll need to export it as a `.ICS` file. Follow these steps:

1. **Open Google Calendar**:
   - Go to [Google Calendar](https://calendar.google.com) and log in to your Google account.

2. **Go to Calendar Settings**:
   - On the left side, find the calendar you want to export under "My calendars."
   - Hover over the calendar name, click the three vertical dots that appear, and choose **Settings and sharing**.

3. **Export the Calendar**:
   - Scroll down to the **Integrate calendar** section.
   - Look for the **Secret address in iCal format**. This is the link to your calendar in `.ICS` format.
   - Copy the link.

4. **Download the .ICS File**:
   - Paste the copied link into your browser's address bar and press **Enter**.
   - The `.ICS` file will be downloaded automatically.

5. **Upload the .ICS File to ARIA**:
   - After you have the `.ICS` file, go back to ARIA and use the **Upload** option to import the file.

Now, your Google Calendar events will be integrated into ARIA, and you can start managing and receiving schedule recommendations.

## Appendix

### Technologies and Tools Used

1. **Streamlit**:
   - **Streamlit** is an open-source framework used to create interactive web applications quickly and easily. In this project, Streamlit is used to build the user interface (UI) where users can interact with ARIA, input schedules, and receive calendar recommendations.

2. **AWS EC2**:
   - **Amazon EC2 (Elastic Compute Cloud)** is a web service that provides resizable compute capacity in the cloud. For deploying the ARIA application, an EC2 instance was used to run the app and make it accessible to users via a web interface.

3. **iCalendar**:
   - **iCalendar** is a file format used to exchange calendar data, such as events, tasks, and to-dos, across different platforms and services. The `.ICS` file format is supported by various calendar applications, including Google Calendar, Microsoft Outlook, and Apple Calendar. ARIA allows users to import and process `.ICS` files to integrate schedules.

4. **Python Libraries and Dependencies**:
   - **openai**: This library is used to integrate OpenAI's API into the ARIA chatbot for natural language processing and task automation.
   - **tiktoken**: A tokenizer used in conjunction with OpenAI models to process text efficiently.
   - **requests**: A simple HTTP library used to make requests to external APIs or services.
   - **python-dotenv**: Helps manage environment variables, allowing the application to securely store sensitive information like API keys and tokens.
   - **icalendar**: A library used to read and write `.ICS` calendar files. This enables ARIA to import and manage calendar data from different sources.
   - **pytz**: A library for timezone management, ensuring that scheduled events and reminders are displayed in the correct time zone.
   - **datetime**: Python’s standard library for working with dates and times.
   - **streamlit-option-menu**: An additional Streamlit library to add option menus and improve user navigation within the web app.
   - **matplotlib**: A data visualization library used for generating graphical representations of data.
   - **pandas**: A powerful data manipulation and analysis library used to work with structured data.
   - **numpy**: A numerical computing library used for handling arrays and matrices efficiently.

5. **GitHub**:
   - The code for this project is hosted on **GitHub**, which allows for version control and collaboration among developers. It provides a platform to manage the project, track issues, and maintain code quality.

### How These Tools Work Together in ARIA:

- **Streamlit** serves as the front-end framework, where users can interact with ARIA through a web interface. Users can upload `.ICS` files, view recommended schedules, and set up reminders.
- **AWS EC2** is used to host and run the application on a cloud-based server, providing scalability and ensuring the app is available for users at any time.
- **iCalendar** is used to allow ARIA to import calendar data from various platforms. Users can upload `.ICS` files containing their schedules, which ARIA processes to provide recommendations and reminders.
- **Python Libraries** such as `openai`, `requests`, `pytz`, and others power the core logic of ARIA, handling everything from API calls and data processing to time zone management and natural language processing.

By integrating these technologies and tools, ARIA provides users with a seamless experience for managing their schedules and organizing their day-to-day tasks.

## Links
- [GitHub Repository](https://github.com/tim6cendekiawan/Team6-CDK-Chatbot)

---


# Copyright
© 2024 **Tim 6 Cendekiawan**. All rights reserved.

This project was developed as part of the **MSIB program** at **RevoU** by **Team 6 Cendekiawan**. We would like to extend our sincere gratitude to our esteemed partners for their continuous support and valuable contributions throughout the development of this project. Their collaboration was instrumental in bringing ARIA to life.

We also wish to express our appreciation to **Amazon Web Services (AWS)** for providing the cloud infrastructure that enables the ARIA application to be deployed, run, and scaled effectively. With AWS’s reliable services, ARIA can remain accessible and perform optimally for users at all times.

All code, content, and materials provided within this repository are the intellectual property of **Tim 6 Cendekiawan**. Unauthorized use, reproduction, or distribution of any part of this repository, including but not limited to the code, designs, documentation, and any other materials, is strictly prohibited. 

**Do not copy, distribute, or use the content of this project without proper permission.** Any attempt to duplicate or redistribute the work contained herein without authorization will be subject to legal action.

© 2024 Tim 6 Cendekiawan. All rights reserved.
