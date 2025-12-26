from dash import html, dcc
import dash_bootstrap_components as dbc

def get_header():
    """App header with branding"""
    return html.Div([
        html.H1("🏃 Krunner", className="app-title"),
        html.P("Your Personal Running Journal", className="app-subtitle")
    ], className="header")

def get_plan_creator():
    """Training plan creation form"""
    return dbc.Card([
        dbc.CardBody([
            html.H3("Create Training Plan", className="section-title"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Plan Name"),
                    dbc.Input(id="plan-name-input", placeholder="e.g., Spring 5K Training", type="text")
                ], md=4),
                dbc.Col([
                    dbc.Label("Weeks Until Race"),
                    dbc.Input(id="plan-weeks-input", placeholder="e.g., 7", type="number", min=1, max=52)
                ], md=4),
                dbc.Col([
                    dbc.Label("Race Distance"),
                    dbc.Input(id="plan-distance-input", placeholder="e.g., 5K", type="text")
                ], md=4),
            ], className="mb-3"),
            dbc.Button("Create Plan", id="create-plan-btn", color="primary", className="create-btn")
        ])
    ], className="plan-creator mb-4")

def get_plan_selector():
    """Dropdown to select active training plan"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Label("Active Training Plan", className="selector-label"),
                dcc.Dropdown(
                    id="plan-selector",
                    placeholder="Select a training plan...",
                    className="plan-dropdown"
                )
            ], md=10),
            dbc.Col([
                dbc.Label("\u00a0", className="selector-label"),  # Spacer for alignment
                dbc.Button("🗑️ Delete Plan", id="delete-plan-btn", color="danger", 
                          className="w-100", style={"marginTop": "0"}, disabled=True)
            ], md=2),
        ])
    ], className="plan-selector mb-4")

def get_training_grid():
    """Training plan grid display"""
    return html.Div([
        html.Div(id="training-grid-container")
    ], className="grid-section")

def create_grid_table(weeks: int, plan_id: str, completed_cells: list):
    """Generate the training grid table"""
    days = ["Day 1: Recovery", "Day 2: Speed", "Day 3: Endurance"]
    
    # Sample workout templates
    workout_templates = {
        1: ["20 min ez", "10 min ez, 10 min (8:30-9 pace), 10 min ez", "3.5 miles"],
        2: ["20 min ez", "10 min ez, 10 min (8:30-9 pace), 10 min ez", "4.5 miles"],
        3: ["25 min ez", "10 min ez, 15 min (8:30-9 pace), 10 min ez", "6 miles"],
        4: ["30 min ez", "10 min ez, 15 min (8:30-9 pace), 10 min ez", "5 miles"],
        5: ["30 min ez", "10 min ez, 15 min (8:30-9 pace), 10 min ez", "5-5.5 miles"],
        6: ["20 min ez", "10 min ez, 15 min (8:30-9 pace), 10 min ez", "4.5 miles"],
        7: ["20 min ez", "20 min ez or rest", "RACE"],
    }
    
    # Header row
    header = html.Tr([
        html.Th("Week", className="grid-header")
    ] + [html.Th(day, className="grid-header") for day in days])
    
    # Data rows
    rows = []
    for week in range(1, weeks + 1):
        cells = [html.Td(f"Week {week}", className="week-label")]
        
        template = workout_templates.get(week, ["Easy run", "Tempo run", "Long run"])
        
        for day_idx, day_workout in enumerate(template[:3]):
            is_completed = (week, day_idx + 1) in completed_cells
            cell_class = "grid-cell completed" if is_completed else "grid-cell"
            
            cells.append(
                html.Td(
                    day_workout,
                    className=cell_class,
                    id={"type": "workout-cell", "week": week, "day": day_idx + 1, "plan": plan_id},
                    n_clicks=0
                )
            )
        
        rows.append(html.Tr(cells))
    
    return dbc.Table([
        html.Thead(header),
        html.Tbody(rows)
    ], bordered=True, hover=True, className="training-grid")

def get_workout_modal():
    """Modal for logging workout details"""
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id="modal-title")),
        dbc.ModalBody([
            html.Div([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Actual Time (minutes)"),
                        dbc.Input(id="actual-time", type="number", step=0.1, placeholder="e.g., 30.5")
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Actual Distance"),
                        dbc.Input(id="actual-distance", type="number", step=0.1, placeholder="e.g., 5.2")
                    ], md=6),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Distance Unit"),
                        dcc.Dropdown(
                            id="distance-unit",
                            options=[
                                {"label": "Miles", "value": "miles"},
                                {"label": "Kilometers", "value": "km"}
                            ],
                            value="miles",
                            clearable=False
                        )
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Actual Pace (min per unit)"),
                        dbc.Input(id="actual-pace", type="number", step=0.1, placeholder="e.g., 8.5")
                    ], md=6),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Intensity"),
                        html.Div([
                            dcc.Slider(
                                id="intensity-slider",
                                min=1,
                                max=5,
                                step=1,
                                value=3,
                                marks={
                                    1: "Very Light",
                                    2: "Light",
                                    3: "Moderate",
                                    4: "Hard",
                                    5: "Very Intense"
                                },
                                className="intensity-slider"
                            )
                        ])
                    ], md=12),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Notes"),
                        dbc.Textarea(
                            id="workout-notes",
                            placeholder="How did the workout feel? Any observations?",
                            style={"height": "100px"}
                        )
                    ], md=12),
                ], className="mb-3"),
                
                # Hidden stores for week, day, plan
                dcc.Store(id="modal-week"),
                dcc.Store(id="modal-day"),
                dcc.Store(id="modal-plan"),
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="modal-cancel", color="secondary", className="me-2"),
            dbc.Button("Save Workout", id="modal-save", color="primary")
        ])
    ], id="workout-modal", size="lg", is_open=False)

def get_layout():
    """Main application layout"""
    return dbc.Container([
        get_header(),
        get_plan_creator(),
        get_plan_selector(),
        get_training_grid(),
        get_workout_modal(),
        
        # Session storage
        dcc.Store(id="session-id", storage_type="local"),
        
        # Toast for notifications
        html.Div(id="notification-container")
    ], fluid=True, className="main-container")
