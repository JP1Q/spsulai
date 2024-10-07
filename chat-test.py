import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import requests
import json

# Initialize the Dash app with a minimal Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define the layout of the app
app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(html.H1("Llama2 Uncensored API Interface", className="text-center mt-4 text-white")),
        ),
        # Message history area
        dbc.Row(
            dbc.Col(
                html.Div(
                    id="message-history",
                    children=[],  # Initialize as empty list
                    style={
                        'marginTop': '20px', 'whiteSpace': 'pre-line',
                        'border': '1px solid white', 'border-radius': '15px',
                        'padding': '20px', 'color': 'white', 'background-color': 'black',
                        'height': '400px', 'overflow-y': 'auto'
                    }
                ),
                width={"size": 6, "offset": 3},
            ),
        ),
        # Input and Button in the same row, at the bottom
        dbc.Row(
            dbc.Col(
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Input(
                                id="user-input",
                                type="text",
                                placeholder="Try asking something...",
                                style={'width': '100%', 'padding': '10px', 'color': 'white', 'background-color': 'black', 'border-radius': '15px', 'border': '1px solid white'},
                            ),
                            width=10,  # Input field takes up 10 out of 12 columns
                        ),
                        dbc.Col(
                            dbc.Button("Send", id="submit-button", color="light", className="rgb-button", style={'width': '100%', 'border-radius': '15px'}),
                            width=2,  # Button takes up 2 out of 12 columns
                        ),
                    ]
                ),
                width={"size": 6, "offset": 3},  # Same width and offset as the output area
                className="mb-4"
            ),
        ),
        dcc.Interval(id='auto-scroll', interval=100, n_intervals=0),  # Timer for auto-scrolling
    ],
    fluid=True,
)

# Add a CSS style to the entire body and custom button hover effect
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Dash App</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                background-color: black;
                color: white;
            }
            .rgb-button {
                border: 5px solid white;
                border-radius: 15px;
                transition: border 0.4s;
            }
            .rgb-button:hover {
                border: 5px solid;
                border-color: pink;
                border-radius: 15px; /* Ensure radius is consistent */
            }
            .message-container {
                display: flex;
                justify-content: space-between; /* Distributes space evenly */
                margin: 5px 0; /* Margin between messages */
            }
            .user-message {
                background-color: blue;
                color: white;
                padding: 10px;
                border-radius: 10px;
                max-width: 70%; /* Limit message width */
                align-self: flex-end; /* Align user messages to the end (right) */
            }
            .ai-message {
                background-color: gray;
                color: white;
                padding: 10px;
                border-radius: 10px;
                max-width: 70%; /* Limit message width */
                align-self: flex-start; /* Align AI messages to the start (left) */
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
        <script>
            // JavaScript to auto-scroll the message history
            const messageHistory = document.getElementById('message-history');
            const autoScroll = () => {
                messageHistory.scrollTop = messageHistory.scrollHeight;
            };
            window.addEventListener('DOMContentLoaded', (event) => {
                const intervalId = setInterval(autoScroll, 100); // Scroll every 100 ms
                // Clear interval on component unload
                window.onbeforeunload = () => {
                    clearInterval(intervalId);
                };
            });
        </script>
    </body>
</html>
'''

# Callback to handle user input, show "Llama is thinking...", and fetch response from the API
@app.callback(
    Output("message-history", "children"),
    Input("submit-button", "n_clicks"),
    Input("user-input", "n_submit"),  # Handle Enter key
    State("user-input", "value"),
    State("message-history", "children"),
    prevent_initial_call=True  # prevents callback firing on app start
)
def generate_response(n_clicks, n_submit, user_input, message_history):
    if not user_input:
        return message_history  # Return previous history if no input

    # Add user's message immediately to the history
    user_message = f"**User:** {user_input}"
    formatted_user_message = html.Div(
        children=[html.Div(dcc.Markdown(user_message), className='user-message')],
        className='message-container'
    )

    # Display "Llama is thinking..." message
    thinking_message = html.Div(
        children=[html.Div("Llama is thinking...", className='ai-message')],
        className='message-container'
    )

    # Update message history to include user's message and the "thinking" message
    updated_history = message_history + [formatted_user_message, thinking_message]

    # Immediately return this updated history to show it in the UI while processing
    # The following long task of calling API happens in background
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "tinyllama",
        "prompt": user_input
    }

    complete_response = ""
    token_details = []
    total_tokens = 0
    eval_duration = 0
    tokens_per_second = 0

    try:
        response = requests.post(url, json=payload, stream=True)

        # Check if the response is NDJSON
        if response.headers.get('Content-Type') == 'application/x-ndjson':
            for line in response.iter_lines():
                if line:
                    json_line = json.loads(line)
                    current_token = json_line.get("response", "")
                    complete_response += current_token

                    # Store the token details
                    token_details.append(current_token)

                    # Update token statistics
                    if json_line.get("done", False):
                        total_tokens = json_line.get("prompt_eval_count", 0)
                        eval_duration = json_line.get("eval_duration", 1)
                        tokens_per_second = total_tokens / (eval_duration / 1e9)

            # Prepare final output after completion
            ai_response = f"**Response:**\n\n{''.join(token_details)}"

            formatted_ai_response = html.Div(
                children=[html.Div(dcc.Markdown(ai_response), className='ai-message')],
                className='message-container'
            )

            # Replace the "thinking" message with the actual response
            updated_history[-1] = formatted_ai_response

            return updated_history

        else:
            return message_history + [html.Div(f"Error: Unexpected content type: {response.headers.get('Content-Type')}\n\n")]

    except requests.exceptions.RequestException as e:
        return message_history + [html.Div(f"Error: Could not connect to the API.\n{str(e)}\n\n")]

# Callback to clear the input field after submission
@app.callback(
    Output("user-input", "value"),
    Input("submit-button", "n_clicks"),
    Input("user-input", "n_submit"),  # Handle Enter key
    prevent_initial_call=True  # Prevent callback from firing on app start
)
def clear_input(n_clicks, n_submit):
    return ""  # Clear the input field

# Run the Dash app
if __name__ == "__main__":
    app.run_server(debug=True)
