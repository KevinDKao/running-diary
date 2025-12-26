import dash
import dash_bootstrap_components as dbc
from database import Database
from layouts import get_layout
from callbacks import register_callbacks

# Initialize database
db = Database("krunner.db")

# Initialize Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="Krunner - Running Journal"
)

# Set layout
app.layout = get_layout()

# Register callbacks
register_callbacks(app, db)

if __name__ == "__main__":
    print("🏃 Starting Krunner...")
    print("📍 Navigate to: http://localhost:8050")
    app.run(debug=True, host="0.0.0.0", port=8050)
