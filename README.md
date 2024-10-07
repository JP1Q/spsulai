
# SPSUL AI

Built using [Dash](https://plotly.com/dash/) and [Dash Bootstrap Components](https://dash-bootstrap-components.opensource.faculty.ai/). This app allows users to send prompts and receive responses from a language model in real-time, with a sleek, responsive UI.

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Dependencies](#dependencies)
- [Contributors](#contributors)

## Features
- **User-friendly Interface**: A simple, clean interface with message bubbles for both user and AI responses.
- **Real-Time Response**: Users receive the AI's response in real time while a "Llama is thinking..." message is displayed during processing.
- **API Integration**: Connects to the Llama2 API to fetch text completions based on user prompts.
- **Auto-scrolling**: Automatically scrolls to the latest message for a seamless experience.
- **Styling**: Custom CSS for dark theme, message formatting, and button hover effects.

## Installation

### Prerequisites
Ensure that you have the following installed:
- Python 3.8+
- `pip`

### Clone the repository
```bash
git clone https://github.com/yourusername/llama2-dash-app.git
cd llama2-dash-app
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run the app
Make sure the Llama2 API server is running locally on port 11434. Then start the Dash app:
```bash
python app.py
```

The app will be accessible at `http://127.0.0.1:8050/` in your web browser.

## Usage
1. Open the app in a browser.
2. Enter a prompt in the text input field at the bottom of the screen.
3. Click the "Send" button or press Enter.
4. The app will display your message and a "Llama is thinking..." message while waiting for the API response.
5. Once the response is received, it will replace the "thinking" message in the chat window.

## Dependencies
The project relies on the following Python packages:
- [Dash](https://dash.plotly.com/) - Web framework for building analytical web applications.
- [Dash Bootstrap Components](https://dash-bootstrap-components.opensource.faculty.ai/) - Bootstrap components for styling Dash apps.
- [requests](https://docs.python-requests.org/en/latest/) - Library for making HTTP requests.

Install them using `pip`:
```bash
pip install dash dash-bootstrap-components requests
```

Ensure your Llama API server is running at this address. You may also need to modify the API `payload` structure according to your specific model and server configuration.

## Contributors
- **Poloha** - Initial development


