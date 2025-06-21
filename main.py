import os
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
import sqlite3
import json
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__, static_folder='dist', static_url_path='')
CORS(app)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_development")

# Database configuration
DATABASE_PATH = "income_tracker.db"

class IncomeTracker:
    def __init__(self):
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Drop existing tables to recreate with new schema
        cursor.execute("DROP TABLE IF EXISTS daily_logs")
        cursor.execute("DROP TABLE IF EXISTS goal_history") 
        cursor.execute("DROP TABLE IF EXISTS income_sources")
        
        # Income sources table (Ver.1 enhanced)
        cursor.execute("""
            CREATE TABLE income_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('Fixed Unit', 'Daily Input', 'Passive')),
                unit_price REAL,
                goal_amount REAL NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Goal history table (Ver.1 enhanced)
        cursor.execute("""
            CREATE TABLE goal_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                income_id INTEGER,
                old_goal_amount REAL,
                new_goal_amount REAL,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (income_id) REFERENCES income_sources (id)
            )
        """)
        
        # Daily task logs (Ver.1 enhanced)
        cursor.execute("""
            CREATE TABLE daily_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                income_id INTEGER,
                task_name TEXT NOT NULL,
                task_count INTEGER,
                amount REAL DEFAULT 0,
                progress_percent INTEGER DEFAULT 0,
                mood_score INTEGER DEFAULT 3,
                note TEXT,
                date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (income_id) REFERENCES income_sources (id)
            )
        """)
        
        # Insert sample data to demonstrate the system
        cursor.execute("""
            INSERT INTO income_sources (name, type, goal_amount, unit_price, description)
            VALUES 
                ('FANZA出版', 'Fixed Unit', 30000, 100, 'デジタル出版による収入'),
                ('フリーライティング', 'Fixed Unit', 50000, 5000, 'ライティング案件'),
                ('Uber Eats', 'Daily Input', 25000, NULL, '配達による日次収入')
        """)
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(DATABASE_PATH)
    
    def dict_factory(self, cursor, row):
        """Convert SQLite row to dictionary"""
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

# Initialize tracker
tracker = IncomeTracker()

# Serve React app
@app.route('/')
def serve():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if path != "" and os.path.exists('static/' + path):
        return send_from_directory('static', path)
    else:
        return send_from_directory('static', 'index.html')

@app.route("/api/income-sources", methods=["GET"])
def get_income_sources():
    """Get all income sources"""
    conn = tracker.get_connection()
    conn.row_factory = tracker.dict_factory
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM income_sources ORDER BY created_at DESC")
    sources = cursor.fetchall()
    conn.close()
    
    return jsonify({"success": True, "data": sources})

@app.route("/api/income-sources", methods=["POST"])
def create_income_source():
    """Create new income source (Ver.1 enhanced)"""
    data = request.get_json()
    
    if not data.get("name") or not data.get("goal_amount") or not data.get("type"):
        return jsonify({"success": False, "error": "Name, goal amount and type are required"}), 400
    
    # Validate type
    if data["type"] not in ["Fixed Unit", "Daily Input", "Passive"]:
        return jsonify({"success": False, "error": "Invalid income type"}), 400
    
    # Validate unit_price for Fixed Unit type
    if data["type"] == "Fixed Unit" and not data.get("unit_price"):
        return jsonify({"success": False, "error": "Unit price required for Fixed Unit type"}), 400
    
    conn = tracker.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO income_sources (name, type, goal_amount, unit_price, description)
        VALUES (?, ?, ?, ?, ?)
    """, (
        data["name"],
        data["type"],
        float(data["goal_amount"]),
        float(data.get("unit_price", 0)) if data.get("unit_price") else None,
        data.get("description", "")
    ))
    
    source_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "data": {"id": source_id}})

@app.route("/api/income-sources/<int:source_id>", methods=["PUT"])
def update_income_source(source_id):
    """Update income source (Ver.1 enhanced with goal history)"""
    data = request.get_json()
    
    conn = tracker.get_connection()
    cursor = conn.cursor()
    
    # Get current goal for history tracking
    cursor.execute("SELECT goal_amount FROM income_sources WHERE id = ?", (source_id,))
    current = cursor.fetchone()
    
    if not current:
        conn.close()
        return jsonify({"success": False, "error": "Income source not found"}), 404
    
    old_goal = current[0]
    new_goal = float(data.get("goal_amount", old_goal))
    
    # Record goal change in history if changed
    if old_goal != new_goal:
        cursor.execute("""
            INSERT INTO goal_history (income_id, old_goal_amount, new_goal_amount)
            VALUES (?, ?, ?)
        """, (source_id, old_goal, new_goal))
    
    # Update source
    cursor.execute("""
        UPDATE income_sources 
        SET name = ?, type = ?, goal_amount = ?, unit_price = ?, description = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        data.get("name"),
        data.get("type"),
        new_goal,
        float(data.get("unit_price", 0)) if data.get("unit_price") else None,
        data.get("description", ""),
        source_id
    ))
    
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

@app.route("/api/income-sources/<int:source_id>", methods=["DELETE"])
def delete_income_source(source_id):
    """Delete income source"""
    conn = tracker.get_connection()
    cursor = conn.cursor()
    
    # Delete related records
    cursor.execute("DELETE FROM daily_logs WHERE source_id = ?", (source_id,))
    cursor.execute("DELETE FROM goal_history WHERE source_id = ?", (source_id,))
    cursor.execute("DELETE FROM income_sources WHERE id = ?", (source_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

@app.route("/api/daily-logs", methods=["GET"])
def get_daily_logs():
    """Get daily logs with optional filtering"""
    date_filter = request.args.get("date")
    source_id = request.args.get("source_id")
    
    conn = tracker.get_connection()
    conn.row_factory = tracker.dict_factory
    cursor = conn.cursor()
    
    query = """
        SELECT dl.*, is.name as source_name 
        FROM daily_logs dl
        LEFT JOIN income_sources is ON dl.income_id = is.id
        WHERE 1=1
    """
    params = []
    
    if date_filter:
        query += " AND dl.date = ?"
        params.append(date_filter)
    
    if source_id:
        query += " AND dl.income_id = ?"
        params.append(int(source_id))
    
    query += " ORDER BY dl.date DESC, dl.created_at DESC"
    
    cursor.execute(query, params)
    logs = cursor.fetchall()
    conn.close()
    
    return jsonify({"success": True, "data": logs})

@app.route("/api/daily-logs", methods=["POST"])
def create_daily_log():
    """Create new daily task log (Ver.1 enhanced)"""
    data = request.get_json()
    
    required_fields = ["income_id", "date", "task_name"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"success": False, "error": f"{field} is required"}), 400
    
    conn = tracker.get_connection()
    cursor = conn.cursor()
    
    # Get income type to calculate amount
    cursor.execute("SELECT type, unit_price FROM income_sources WHERE id = ?", (int(data["income_id"]),))
    income_info = cursor.fetchone()
    
    if not income_info:
        conn.close()
        return jsonify({"success": False, "error": "Income source not found"}), 404
    
    income_type, unit_price = income_info
    calculated_amount = 0
    
    # Calculate amount based on income type
    if income_type == "Fixed Unit" and unit_price and data.get("task_count"):
        calculated_amount = unit_price * int(data["task_count"])
    elif income_type in ["Daily Input", "Passive"] and data.get("amount"):
        calculated_amount = float(data["amount"])
    
    cursor.execute("""
        INSERT INTO daily_logs 
        (income_id, date, task_name, task_count, amount, progress_percent, mood_score, note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        int(data["income_id"]),
        data["date"],
        data["task_name"],
        int(data.get("task_count", 0)) if data.get("task_count") else None,
        calculated_amount,
        int(data.get("progress_percent", 0)),
        int(data.get("mood_score", 3)),
        data.get("note", "")
    ))
    
    log_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "data": {"id": log_id}})

@app.route("/api/daily-logs/<int:log_id>", methods=["PUT"])
def update_daily_log(log_id):
    """Update daily task log (Ver.1 enhanced)"""
    data = request.get_json()
    
    conn = tracker.get_connection()
    cursor = conn.cursor()
    
    # Get income type to calculate amount
    cursor.execute("SELECT type, unit_price FROM income_sources WHERE id = ?", (int(data["income_id"]),))
    income_info = cursor.fetchone()
    
    if not income_info:
        conn.close()
        return jsonify({"success": False, "error": "Income source not found"}), 404
    
    income_type, unit_price = income_info
    calculated_amount = 0
    
    # Calculate amount based on income type
    if income_type == "Fixed Unit" and unit_price and data.get("task_count"):
        calculated_amount = unit_price * int(data["task_count"])
    elif income_type in ["Daily Input", "Passive"] and data.get("amount"):
        calculated_amount = float(data["amount"])
    
    cursor.execute("""
        UPDATE daily_logs 
        SET income_id = ?, date = ?, task_name = ?, task_count = ?, 
            amount = ?, progress_percent = ?, mood_score = ?, note = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        int(data["income_id"]),
        data["date"],
        data["task_name"],
        int(data.get("task_count", 0)) if data.get("task_count") else None,
        calculated_amount,
        int(data.get("progress_percent", 0)),
        int(data.get("mood_score", 3)),
        data.get("note", ""),
        log_id
    ))
    
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

@app.route("/api/daily-logs/<int:log_id>", methods=["DELETE"])
def delete_daily_log(log_id):
    """Delete daily log"""
    conn = tracker.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM daily_logs WHERE id = ?", (log_id,))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

@app.route("/api/dashboard", methods=["GET"])
def get_dashboard_data():
    """Get comprehensive dashboard data (Ver.2 enhanced with visual feedback)"""
    conn = tracker.get_connection()
    conn.row_factory = tracker.dict_factory
    cursor = conn.cursor()
    
    # Get current month's data
    current_month = datetime.now().strftime("%Y-%m")
    today = datetime.now().date()
    days_in_month = (datetime.now().replace(month=datetime.now().month % 12 + 1, day=1) - timedelta(days=1)).day
    current_day = today.day
    days_remaining = days_in_month - current_day
    
    # Get income sources with progress
    cursor.execute("SELECT * FROM income_sources ORDER BY created_at DESC")
    sources = cursor.fetchall()
    
    dashboard_data = {
        "total_earned": 0,
        "total_goal": 0,
        "overall_progress": 0,
        "days_remaining": days_remaining,
        "current_day": current_day,
        "days_in_month": days_in_month,
        "sources": [],
        "alerts": [],
        "recovery_plans": [],
        "global_summary": {}
    }
    
    for source in sources:
        # Get current month's earnings for this source
        cursor.execute("""
            SELECT SUM(amount) as total_earned, COUNT(*) as task_count, AVG(mood_score) as avg_mood
            FROM daily_logs 
            WHERE income_id = ? AND date LIKE ?
        """, (source["id"], f"{current_month}%"))
        
        earnings_data = cursor.fetchone()
        earned = earnings_data["total_earned"] or 0
        task_count = earnings_data["task_count"] or 0
        avg_mood = earnings_data["avg_mood"] or 3
        
        progress_percent = (earned / source["goal_amount"] * 100) if source["goal_amount"] > 0 else 0
        completion_rate = progress_percent / 100
        
        # Calculate required daily pace
        remaining_amount = max(0, source["goal_amount"] - earned)
        required_daily_pace = remaining_amount / max(1, days_remaining)
        
        # Determine alert level
        expected_progress = (current_day / days_in_month * 100)
        alert_level = "none"
        if progress_percent < expected_progress - 20:
            alert_level = "high"
        elif progress_percent < expected_progress - 10:
            alert_level = "medium"
        elif progress_percent < expected_progress:
            alert_level = "low"
        
        source_data = {
            **source,
            "earned_amount": earned,
            "completion_rate": completion_rate,
            "progress_percent": progress_percent,
            "task_count": task_count,
            "avg_mood": avg_mood,
            "remaining_amount": remaining_amount,
            "required_daily_pace": required_daily_pace,
            "alert_level": alert_level,
            "is_behind_target": progress_percent < expected_progress
        }
        
        dashboard_data["sources"].append(source_data)
        dashboard_data["total_earned"] += earned
        dashboard_data["total_goal"] += source["goal_amount"]
        
        # Generate alerts for behind targets (Ver.3 shortfall detection)
        if alert_level in ["medium", "high"]:
            shortfall = remaining_amount
            
            # Calculate catch-up scenario
            if source["type"] == "Fixed Unit" and source["unit_price"]:
                current_daily_avg = earned / max(1, current_day)
                required_multiplier = required_daily_pace / max(1, current_daily_avg)
                catch_up_message = f"Do {required_multiplier:.1f}x more daily tasks for {days_remaining} days"
            else:
                catch_up_message = f"Earn ¥{required_daily_pace:.0f}/day for {days_remaining} days"
            
            # Calculate likelihood (basic simulation)
            current_pace = earned / max(1, current_day)
            likelihood = min(100, (current_pace * days_in_month / source["goal_amount"]) * 100)
            
            dashboard_data["recovery_plans"].append({
                "income_name": source["name"],
                "shortfall": shortfall,
                "catch_up_message": catch_up_message,
                "likelihood": likelihood,
                "severity": alert_level
            })
    
    # Global summary calculations
    dashboard_data["overall_progress"] = (dashboard_data["total_earned"] / dashboard_data["total_goal"] * 100) if dashboard_data["total_goal"] > 0 else 0
    
    dashboard_data["global_summary"] = {
        "total_behind_target": len([s for s in dashboard_data["sources"] if s["is_behind_target"]]),
        "avg_completion_rate": sum([s["completion_rate"] for s in dashboard_data["sources"]]) / len(dashboard_data["sources"]) if dashboard_data["sources"] else 0,
        "total_required_daily": sum([s["required_daily_pace"] for s in dashboard_data["sources"]])
    }
    
    conn.close()
    return jsonify({"success": True, "data": dashboard_data})

@app.route("/api/analytics", methods=["GET"])
def get_analytics():
    """Get analytics data for charts (Ver.2 enhanced graphs)"""
    period = request.args.get("period", "week")
    
    conn = tracker.get_connection()
    conn.row_factory = tracker.dict_factory
    cursor = conn.cursor()
    
    analytics = {}
    
    if period == "week":
        # Last 7 days daily income trend
        cursor.execute("""
            SELECT date, SUM(amount) as daily_total, COUNT(*) as task_count
            FROM daily_logs 
            WHERE date >= date('now', '-7 days')
            GROUP BY date
            ORDER BY date
        """)
        daily_data = cursor.fetchall()
        
        # Weekly task volume by income source
        cursor.execute("""
            SELECT is.name, SUM(dl.task_count) as total_tasks, SUM(dl.amount) as total_amount
            FROM daily_logs dl
            JOIN income_sources is ON dl.income_id = is.id
            WHERE dl.date >= date('now', '-7 days')
            GROUP BY is.name
            ORDER BY total_amount DESC
        """)
        weekly_volume = cursor.fetchall()
        
    elif period == "month":
        # Last 30 days
        cursor.execute("""
            SELECT date, SUM(amount) as daily_total, COUNT(*) as task_count
            FROM daily_logs 
            WHERE date >= date('now', '-30 days')
            GROUP BY date
            ORDER BY date
        """)
        daily_data = cursor.fetchall()
        
        # Monthly task volume
        cursor.execute("""
            SELECT is.name, SUM(dl.task_count) as total_tasks, SUM(dl.amount) as total_amount
            FROM daily_logs dl
            JOIN income_sources is ON dl.income_id = is.id
            WHERE dl.date >= date('now', '-30 days')
            GROUP BY is.name
            ORDER BY total_amount DESC
        """)
        weekly_volume = cursor.fetchall()
    
    # Mood vs Productivity correlation (always calculated)
    cursor.execute("""
        SELECT mood_score, AVG(amount) as avg_earnings, COUNT(*) as count
        FROM daily_logs 
        WHERE date >= date('now', '-30 days') AND amount > 0
        GROUP BY mood_score
        ORDER BY mood_score
    """)
    mood_performance = cursor.fetchall()
    
    # Income source performance comparison
    cursor.execute("""
        SELECT 
            is.name,
            is.goal_amount,
            COALESCE(SUM(dl.amount), 0) as earned,
            COUNT(dl.id) as task_days,
            AVG(dl.mood_score) as avg_mood
        FROM income_sources is
        LEFT JOIN daily_logs dl ON is.id = dl.income_id 
            AND dl.date >= date('now', 'start of month')
        GROUP BY is.id, is.name, is.goal_amount
        ORDER BY earned DESC
    """)
    income_performance = cursor.fetchall()
    
    analytics = {
        "daily_income_trend": daily_data,
        "mood_productivity_correlation": mood_performance,
        "weekly_task_volume": weekly_volume,
        "income_performance": income_performance,
        "period": period
    }
    
    conn.close()
    return jsonify({"success": True, "data": analytics})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)