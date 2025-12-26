import sqlite3
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class Database:
    def __init__(self, db_path: str = "krunner.db"):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Training plans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS training_plans (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                name TEXT NOT NULL,
                weeks INTEGER NOT NULL,
                race_distance TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Workout logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workout_logs (
                id TEXT PRIMARY KEY,
                plan_id TEXT NOT NULL,
                week INTEGER NOT NULL,
                day INTEGER NOT NULL,
                actual_time REAL,
                actual_distance REAL,
                actual_pace REAL,
                distance_unit TEXT DEFAULT 'miles',
                intensity INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plan_id) REFERENCES training_plans(id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # Training Plans
    def create_plan(self, session_id: str, name: str, weeks: int, race_distance: str) -> str:
        """Create a new training plan"""
        plan_id = str(uuid.uuid4())
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO training_plans (id, session_id, name, weeks, race_distance)
            VALUES (?, ?, ?, ?, ?)
        ''', (plan_id, session_id, name, weeks, race_distance))
        
        conn.commit()
        conn.close()
        return plan_id
    
    def get_plans(self, session_id: str) -> List[Dict]:
        """Get all training plans for a session"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM training_plans 
            WHERE session_id = ?
            ORDER BY created_at DESC
        ''', (session_id,))
        
        plans = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return plans
    
    def get_plan(self, plan_id: str) -> Optional[Dict]:
        """Get a specific training plan"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM training_plans WHERE id = ?', (plan_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def delete_plan(self, plan_id: str) -> bool:
        """Delete a training plan and all associated workout logs"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Delete workout logs first
        cursor.execute('DELETE FROM workout_logs WHERE plan_id = ?', (plan_id,))
        
        # Delete the plan
        cursor.execute('DELETE FROM training_plans WHERE id = ?', (plan_id,))
        
        conn.commit()
        rows_deleted = cursor.rowcount
        conn.close()
        
        return rows_deleted > 0
    
    # Workout Logs
    def save_workout_log(self, plan_id: str, week: int, day: int, 
                        actual_time: Optional[float] = None,
                        actual_distance: Optional[float] = None,
                        actual_pace: Optional[float] = None,
                        distance_unit: str = 'miles',
                        intensity: Optional[int] = None,
                        notes: str = '') -> str:
        """Save or update a workout log"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if log exists
        cursor.execute('''
            SELECT id FROM workout_logs 
            WHERE plan_id = ? AND week = ? AND day = ?
        ''', (plan_id, week, day))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing log
            log_id = existing['id']
            cursor.execute('''
                UPDATE workout_logs 
                SET actual_time = ?, actual_distance = ?, actual_pace = ?,
                    distance_unit = ?, intensity = ?, notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (actual_time, actual_distance, actual_pace, distance_unit, 
                  intensity, notes, log_id))
        else:
            # Create new log
            log_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO workout_logs 
                (id, plan_id, week, day, actual_time, actual_distance, 
                 actual_pace, distance_unit, intensity, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (log_id, plan_id, week, day, actual_time, actual_distance,
                  actual_pace, distance_unit, intensity, notes))
        
        conn.commit()
        conn.close()
        return log_id
    
    def get_workout_log(self, plan_id: str, week: int, day: int) -> Optional[Dict]:
        """Get a specific workout log"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM workout_logs 
            WHERE plan_id = ? AND week = ? AND day = ?
        ''', (plan_id, week, day))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_all_logs_for_plan(self, plan_id: str) -> List[Dict]:
        """Get all workout logs for a plan"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM workout_logs 
            WHERE plan_id = ?
            ORDER BY week, day
        ''', (plan_id,))
        
        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return logs
    
    def get_completed_cells(self, plan_id: str) -> List[Tuple[int, int]]:
        """Get list of (week, day) tuples that have completed logs"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT week, day FROM workout_logs 
            WHERE plan_id = ?
        ''', (plan_id,))
        
        cells = [(row['week'], row['day']) for row in cursor.fetchall()]
        conn.close()
        return cells
