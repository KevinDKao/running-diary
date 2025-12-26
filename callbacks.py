from dash import Input, Output, State, ALL, ctx, no_update
import dash_bootstrap_components as dbc
from dash import html
import uuid
from database import Database
from layouts import create_grid_table

def register_callbacks(app, db: Database):
    """Register all application callbacks"""
    
    # Initialize session ID
    @app.callback(
        Output("session-id", "data"),
        Input("session-id", "data")
    )
    def init_session(session_data):
        if session_data is None:
            return str(uuid.uuid4())
        return session_data
    
    # Create training plan
    @app.callback(
        [Output("plan-selector", "options"),
         Output("plan-selector", "value"),
         Output("plan-name-input", "value"),
         Output("plan-weeks-input", "value"),
         Output("plan-distance-input", "value"),
         Output("notification-container", "children")],
        Input("create-plan-btn", "n_clicks"),
        [State("plan-name-input", "value"),
         State("plan-weeks-input", "value"),
         State("plan-distance-input", "value"),
         State("session-id", "data"),
         State("plan-selector", "value")],
        prevent_initial_call=True
    )
    def create_plan(n_clicks, name, weeks, distance, session_id, current_plan):
        if not all([name, weeks, distance]):
            toast = dbc.Toast(
                "Please fill in all fields",
                header="Error",
                icon="danger",
                duration=3000,
                is_open=True
            )
            return no_update, no_update, no_update, no_update, no_update, toast
        
        plan_id = db.create_plan(session_id, name, weeks, distance)
        plans = db.get_plans(session_id)
        
        options = [{"label": p["name"], "value": p["id"]} for p in plans]
        
        toast = dbc.Toast(
            f"Training plan '{name}' created successfully!",
            header="Success",
            icon="success",
            duration=3000,
            is_open=True,
            style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999}
        )
        
        return options, plan_id, "", None, "", toast
    
    # Update plan selector on load
    @app.callback(
        Output("plan-selector", "options", allow_duplicate=True),
        Input("session-id", "data"),
        prevent_initial_call=True
    )
    def load_plans(session_id):
        if session_id:
            plans = db.get_plans(session_id)
            return [{"label": p["name"], "value": p["id"]} for p in plans]
        return []
    
    # Enable/disable delete button based on plan selection
    @app.callback(
        Output("delete-plan-btn", "disabled"),
        Input("plan-selector", "value")
    )
    def toggle_delete_button(plan_id):
        return plan_id is None
    
    # Delete training plan
    @app.callback(
        [Output("plan-selector", "options", allow_duplicate=True),
         Output("plan-selector", "value", allow_duplicate=True),
         Output("training-grid-container", "children", allow_duplicate=True),
         Output("notification-container", "children", allow_duplicate=True)],
        Input("delete-plan-btn", "n_clicks"),
        [State("plan-selector", "value"),
         State("session-id", "data")],
        prevent_initial_call=True
    )
    def delete_plan(n_clicks, plan_id, session_id):
        if not plan_id:
            return no_update, no_update, no_update, no_update
        
        # Get plan name before deleting
        plan = db.get_plan(plan_id)
        plan_name = plan["name"] if plan else "Unknown"
        
        # Delete the plan
        db.delete_plan(plan_id)
        
        # Reload plans
        plans = db.get_plans(session_id)
        options = [{"label": p["name"], "value": p["id"]} for p in plans]
        
        # Clear grid
        empty_grid = html.Div("Select a training plan to view the schedule", 
                             className="text-muted text-center p-5")
        
        # Success notification
        toast = dbc.Toast(
            f"Training plan '{plan_name}' deleted successfully!",
            header="Deleted",
            icon="success",
            duration=3000,
            is_open=True,
            style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999}
        )
        
        return options, None, empty_grid, toast
    
    # Display training grid when plan is selected
    @app.callback(
        Output("training-grid-container", "children"),
        Input("plan-selector", "value"),
        prevent_initial_call=True
    )
    def display_grid(plan_id):
        if not plan_id:
            return html.Div("Select a training plan to view the schedule", 
                          className="text-muted text-center p-5")
        
        plan = db.get_plan(plan_id)
        if not plan:
            return html.Div("Plan not found", className="text-muted text-center p-5")
        
        completed_cells = db.get_completed_cells(plan_id)
        return create_grid_table(plan["weeks"], plan_id, completed_cells)
    
    # Open workout modal when cell is clicked
    @app.callback(
        [Output("workout-modal", "is_open"),
         Output("modal-title", "children"),
         Output("modal-week", "data"),
         Output("modal-day", "data"),
         Output("modal-plan", "data"),
         Output("actual-time", "value"),
         Output("actual-distance", "value"),
         Output("actual-pace", "value"),
         Output("distance-unit", "value"),
         Output("intensity-slider", "value"),
         Output("workout-notes", "value")],
        [Input({"type": "workout-cell", "week": ALL, "day": ALL, "plan": ALL}, "n_clicks"),
         Input("modal-cancel", "n_clicks"),
         Input("modal-save", "n_clicks")],
        [State("modal-week", "data"),
         State("modal-day", "data"),
         State("modal-plan", "data"),
         State("actual-time", "value"),
         State("actual-distance", "value"),
         State("actual-pace", "value"),
         State("distance-unit", "value"),
         State("intensity-slider", "value"),
         State("workout-notes", "value")],
        prevent_initial_call=True
    )
    def handle_modal(cell_clicks, cancel_clicks, save_clicks, 
                    stored_week, stored_day, stored_plan,
                    time_val, dist_val, pace_val, unit_val, intensity_val, notes_val):
        
        triggered_id = ctx.triggered_id
        
        # Close modal
        if triggered_id == "modal-cancel":
            return False, "", None, None, None, None, None, None, "miles", 3, ""
        
        # Save workout
        if triggered_id == "modal-save":
            if stored_plan and stored_week and stored_day:
                db.save_workout_log(
                    plan_id=stored_plan,
                    week=stored_week,
                    day=stored_day,
                    actual_time=time_val,
                    actual_distance=dist_val,
                    actual_pace=pace_val,
                    distance_unit=unit_val,
                    intensity=intensity_val,
                    notes=notes_val or ""
                )
            return False, "", None, None, None, None, None, None, "miles", 3, ""
        
        # Open modal for cell click
        if isinstance(triggered_id, dict) and triggered_id.get("type") == "workout-cell":
            # Get the index of the clicked cell
            clicked_index = None
            for i, clicks in enumerate(cell_clicks):
                if clicks and clicks > 0:
                    clicked_index = i
                    break
            
            # Only open modal if a cell was actually clicked (not just rendered)
            if clicked_index is None:
                return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
            
            week = triggered_id["week"]
            day = triggered_id["day"]
            plan_id = triggered_id["plan"]
            
            # Check if there's existing log
            existing_log = db.get_workout_log(plan_id, week, day)
            
            day_names = {1: "Recovery", 2: "Speed", 3: "Endurance"}
            title = f"Week {week} - Day {day}: {day_names.get(day, 'Workout')}"
            
            if existing_log:
                return (True, title, week, day, plan_id,
                       existing_log.get("actual_time"),
                       existing_log.get("actual_distance"),
                       existing_log.get("actual_pace"),
                       existing_log.get("distance_unit", "miles"),
                       existing_log.get("intensity", 3),
                       existing_log.get("notes", ""))
            else:
                return True, title, week, day, plan_id, None, None, None, "miles", 3, ""
        
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
    
    # Refresh grid after saving
    @app.callback(
        Output("training-grid-container", "children", allow_duplicate=True),
        Input("modal-save", "n_clicks"),
        [State("modal-plan", "data"),
         State("plan-selector", "value")],
        prevent_initial_call=True
    )
    def refresh_grid_after_save(n_clicks, modal_plan, selected_plan):
        plan_id = modal_plan or selected_plan
        if not plan_id:
            return no_update
        
        plan = db.get_plan(plan_id)
        if not plan:
            return no_update
        
        completed_cells = db.get_completed_cells(plan_id)
        return create_grid_table(plan["weeks"], plan_id, completed_cells)
