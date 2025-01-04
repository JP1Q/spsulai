import dash
from dash import html, dcc, Input, Output, State
import mariadb
import sys

# Database connection configuration
db_config = {
    "user": "your_username",
    "password": "your_password",
    "host": "localhost",
    "port": 3306,
    "database": "school_db"
}

# Connect to MariaDB
def get_db_connection():
    try:
        conn = mariadb.connect(**db_config)
        return conn
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB: {e}")
        sys.exit(1)

# Create the Dash app
app = dash.Dash(__name__)

# Layout for the login page
app.layout = html.Div(
    style={
        "height": "100vh",
        "background-color": "#1a1a2e",
        "display": "flex",
        "justify-content": "center",
        "align-items": "center",
    },
    children=[
        html.Div(
            style={
                "width": "400px",
                "padding": "20px",
                "background-color": "#44475a",
                "border-radius": "12px",
                "box-shadow": "0 4px 8px rgba(0, 0, 0, 0.2)",
                "text-align": "center",
                "color": "white",
            },
            children=[
                html.Div(
                    [
                        html.Div(
                            style={
                                "font-size": "50px",
                                "color": "#ffffff",
                                "margin-bottom": "20px",
                            },
                            children=[
                                html.I(className="dashicons dashicons-admin-users"),
                            ],
                        ),
                        html.H2(
                            "Přihlásit se do spsulai",
                            style={"margin-bottom": "20px", "font-weight": "normal"},
                        ),
                        html.P("version xx.xx.xx", style={"font-size": "12px", "margin-bottom": "20px"}),
                        dcc.Input(
                            id="username",
                            type="text",
                            placeholder="email",
                            style={
                                "margin-bottom": "10px",
                                "width": "100%",
                                "padding": "10px",
                                "border": "none",
                                "border-radius": "8px",
                                "background-color": "#3c3f55",
                                "color": "white",
                                "font-size": "16px",
                            },
                        ),
                        dcc.Input(
                            id="password",
                            type="password",
                            placeholder="heslo (do Bakalářů)",
                            style={
                                "margin-bottom": "10px",
                                "width": "100%",
                                "padding": "10px",
                                "border": "none",
                                "border-radius": "8px",
                                "background-color": "#3c3f55",
                                "color": "white",
                                "font-size": "16px",
                            },
                        ),
                        html.Button(
                            "přihlásit",
                            id="login-btn",
                            n_clicks=0,
                            style={
                                "width": "100%",
                                "padding": "10px",
                                "border": "none",
                                "border-radius": "8px",
                                "background-color": "#6272a4",
                                "color": "white",
                                "font-size": "16px",
                                "cursor": "pointer",
                                "display": "flex",
                                "align-items": "center",
                                "justify-content": "center",
                            },
                            children=[
                                "přihlásit ",
                                html.I(
                                    className="dashicons dashicons-arrow-right-alt",
                                    style={"margin-left": "8px"},
                                ),
                            ],
                        ),
                        html.Div(
                            id="login-message",
                            style={"margin-top": "20px", "color": "red", "font-size": "14px"},
                        ),
                    ]
                )
            ],
        )
    ],
)

# Callback to handle login
@app.callback(
    Output("login-message", "children"),
    Input("login-btn", "n_clicks"),
    State("username", "value"),
    State("password", "value"),
)
def handle_login(n_clicks, username, password):
    if n_clicks > 0:
        if not username or not password:
            return "Please enter both username and password."

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Query to check if the username and password are valid
            cursor.execute(
                "SELECT COUNT(*) FROM studenti WHERE username = ? AND password = ?",
                (username, password),
            )
            result = cursor.fetchone()

            if result and result[0] > 0:
                return "Login successful!"
            else:
                return "Invalid username or password."
        except mariadb.Error as e:
            print(f"Error: {e}")
            return "An error occurred during login."
        finally:
            cursor.close()
            conn.close()

    return ""


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
