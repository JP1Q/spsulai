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
        # Input and Button in the same row, with the same width as output
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
                            dbc.Button("Generate", id="submit-button", color="light", className="rgb-button", style={'width': '100%', 'border-radius': '15px'}),
                            width=2,  # Button takes up 2 out of 12 columns
                        ),
                    ]
                ),
                width={"size": 6, "offset": 3},  # Same width and offset as the output area
                className="mb-4"
            ),
        ),
        # Container where output or loading GIF will be displayed
        dbc.Row(
            dbc.Col(
                dcc.Loading(  # Adding the Loading component
                    id="loading",
                    type="default",  # You can change this to "circle" or "graph" for different styles
                    children=dcc.Markdown(
                        id="output-area", 
                        children="The output will be displayed here.",  # Initial message
                        style={
                            'marginTop': '20px', 'whiteSpace': 'pre-line',
                            'border': '1px solid white', 'border-radius': '15px',
                            'padding': '20px', 'color': 'white', 'background-color': 'black',
                            'width': '100%'
                        }
                    )
                ),
                width={"size": 6, "offset": 3},
            ),
        ),
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
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Callback to handle user input, show loading GIF, and fetch response from the API
@app.callback(
    Output("output-area", "children"),
    Input("submit-button", "n_clicks"),
    State("user-input", "value"),
    prevent_initial_call=True  # prevents callback firing on app start
)
def generate_response(n_clicks, user_input):
    if not user_input:
        return "The output will be displayed here."  # Initial message if no input

    # Stage 2: Call the API to generate a response
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama2-uncensored",
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
            final_output = f"**Response:**\n\n{''.join(token_details)}"
            final_output += f"\n\n**Total Tokens:** {total_tokens}\n**Tokens per Second:** {tokens_per_second:.2f}"

            return final_output
        else:
            return f"Error: Unexpected content type: {response.headers.get('Content-Type')}"

    except requests.exceptions.RequestException as e:
        return f"Error: Could not connect to the API.\n{str(e)}"

# Run the Dash app
if __name__ == "__main__":
    app.run_server(debug=True)
