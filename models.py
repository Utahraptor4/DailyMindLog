import json
import csv
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import calendar

class IncomeGoalManager:
    def __init__(self):
        self.income_sources_file = "income_sources.json"
        self.daily_logs_file = "daily_logs.csv"
        self.settings_file = "app_settings.json"
        self.init_files()
    
    def init_files(self):
        """Initialize all data files if they don't exist"""
        # Income sources file
        if not os.path.exists(self.income_sources_file):
            default_sources = []
            with open(self.income_sources_file, "w", encoding="utf-8") as f:
                json.dump(default_sources, f, ensure_ascii=False, indent=2)
        
        # Daily logs CSV
        if not os.path.exists(self.daily_logs_file):
            with open(self.daily_logs_file, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["id", "date", "source_id", "task_description", "units_completed", "progress_percent", "mood_score", "skip_reason", "created_at"])
        
        # Settings file
        if not os.path.exists(self.settings_file):
            default_settings = {
                "monthly_income_goal": 70000,
                "currency": "yen",
                "created_at": datetime.now().isoformat()
            }
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(default_settings, f, ensure_ascii=False, indent=2)
    
    def get_income_sources(self) -> List[Dict[str, Any]]:
        """Get all income sources"""
        try:
            with open(self.income_sources_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading income sources: {e}")
            return []
    
    def add_income_source(self, name: str, unit_price: int, monthly_target: int, description: str = "") -> bool:
        """Add a new income source"""
        try:
            sources = self.get_income_sources()
            new_id = max([s.get('id', 0) for s in sources], default=0) + 1
            
            new_source = {
                "id": new_id,
                "name": name,
                "unit_price": unit_price,
                "monthly_target": monthly_target,
                "description": description,
                "created_at": datetime.now().isoformat()
            }
            
            sources.append(new_source)
            
            with open(self.income_sources_file, "w", encoding="utf-8") as f:
                json.dump(sources, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Error adding income source: {e}")
            return False
    
    def update_income_source(self, source_id: int, updates: Dict[str, Any]) -> bool:
        """Update an existing income source"""
        try:
            sources = self.get_income_sources()
            for source in sources:
                if source['id'] == source_id:
                    source.update(updates)
                    source['updated_at'] = datetime.now().isoformat()
                    break
            
            with open(self.income_sources_file, "w", encoding="utf-8") as f:
                json.dump(sources, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Error updating income source: {e}")
            return False
    
    def delete_income_source(self, source_id: int) -> bool:
        """Delete an income source"""
        try:
            sources = self.get_income_sources()
            sources = [s for s in sources if s['id'] != source_id]
            
            with open(self.income_sources_file, "w", encoding="utf-8") as f:
                json.dump(sources, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Error deleting income source: {e}")
            return False
    
    def add_daily_log(self, source_id: int, task_description: str, units_completed: int, 
                     progress_percent: int, mood_score: int, skip_reason: str = "") -> bool:
        """Add a daily task log"""
        try:
            log_id = self.get_next_log_id()
            today = datetime.now().strftime("%Y-%m-%d")
            created_at = datetime.now().isoformat()
            
            with open(self.daily_logs_file, "a", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([log_id, today, source_id, task_description, units_completed, 
                               progress_percent, mood_score, skip_reason, created_at])
            
            return True
        except Exception as e:
            print(f"Error adding daily log: {e}")
            return False
    
    def get_next_log_id(self) -> int:
        """Get the next available log ID"""
        try:
            with open(self.daily_logs_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                max_id = 0
                for row in reader:
                    try:
                        current_id = int(row['id'])
                        max_id = max(max_id, current_id)
                    except (ValueError, KeyError):
                        continue
                return max_id + 1
        except Exception:
            return 1
    
    def get_daily_logs(self, date_str: str = None) -> List[Dict[str, Any]]:
        """Get daily logs for a specific date or all logs"""
        logs = []
        if not os.path.exists(self.daily_logs_file):
            return logs
        
        try:
            with open(self.daily_logs_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if date_str is None or row['date'] == date_str:
                        log = {
                            'id': int(row['id']),
                            'date': row['date'],
                            'source_id': int(row['source_id']),
                            'task_description': row['task_description'],
                            'units_completed': int(row['units_completed']),
                            'progress_percent': int(row['progress_percent']),
                            'mood_score': int(row['mood_score']),
                            'skip_reason': row['skip_reason'],
                            'created_at': row['created_at']
                        }
                        logs.append(log)
        except Exception as e:
            print(f"Error reading daily logs: {e}")
        
        return logs
    
    def get_monthly_progress(self) -> Dict[str, Any]:
        """Calculate monthly progress and income"""
        today = datetime.now()
        month_start = today.replace(day=1)
        
        # Get current month logs
        logs = self.get_daily_logs()
        monthly_logs = [log for log in logs if log['date'] >= month_start.strftime("%Y-%m-%d")]
        
        # Get income sources
        sources = self.get_income_sources()
        source_dict = {s['id']: s for s in sources}
        
        # Calculate progress by source
        source_progress = {}
        total_income = 0
        
        for source in sources:
            source_id = source['id']
            source_logs = [log for log in monthly_logs if log['source_id'] == source_id]
            
            units_completed = sum(log['units_completed'] for log in source_logs)
            income_earned = units_completed * source['unit_price']
            target_income = source['monthly_target'] * source['unit_price']
            
            source_progress[source_id] = {
                'name': source['name'],
                'units_completed': units_completed,
                'monthly_target': source['monthly_target'],
                'units_remaining': max(0, source['monthly_target'] - units_completed),
                'income_earned': income_earned,
                'target_income': target_income,
                'completion_rate': (units_completed / source['monthly_target'] * 100) if source['monthly_target'] > 0 else 0
            }
            
            total_income += income_earned
        
        # Get settings
        settings = self.get_settings()
        monthly_goal = settings.get('monthly_income_goal', 70000)
        
        # Calculate overall progress
        overall_progress = (total_income / monthly_goal * 100) if monthly_goal > 0 else 0
        missed_income = max(0, monthly_goal - total_income)
        
        return {
            'total_income': total_income,
            'monthly_goal': monthly_goal,
            'overall_progress': overall_progress,
            'missed_income': missed_income,
            'source_progress': source_progress,
            'days_in_month': calendar.monthrange(today.year, today.month)[1],
            'current_day': today.day
        }
    
    def get_settings(self) -> Dict[str, Any]:
        """Get application settings"""
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading settings: {e}")
            return {"monthly_income_goal": 70000, "currency": "yen"}
    
    def update_settings(self, new_settings: Dict[str, Any]) -> bool:
        """Update application settings"""
        try:
            current_settings = self.get_settings()
            current_settings.update(new_settings)
            current_settings['updated_at'] = datetime.now().isoformat()
            
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(current_settings, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Error updating settings: {e}")
            return False
    
    def get_ai_suggestions(self) -> Dict[str, Any]:
        """Generate AI suggestions based on current progress and mood"""
        progress = self.get_monthly_progress()
        today = datetime.now()
        days_remaining = progress['days_in_month'] - progress['current_day']
        
        suggestions = []
        priorities = []
        
        # Analyze each income source
        for source_id, source_data in progress['source_progress'].items():
            completion_rate = source_data['completion_rate']
            remaining_units = source_data['units_remaining']
            
            if completion_rate < 70 and remaining_units > 0:  # Behind schedule
                daily_needed = remaining_units / max(1, days_remaining)
                suggestions.append(f"{source_data['name']}: 1日あたり{daily_needed:.1f}個のタスクが必要です")
                priorities.append({
                    'source': source_data['name'],
                    'urgency': 'high' if completion_rate < 50 else 'medium',
                    'action': f"今日は{int(daily_needed) + 1}個のタスクを完了してください"
                })
        
        # Overall suggestion
        if progress['overall_progress'] < 70:
            suggestions.append(f"目標達成まで{progress['missed_income']:,}円不足しています。優先タスクに集中しましょう。")
        
        # Get recent mood data
        recent_logs = self.get_daily_logs(today.strftime("%Y-%m-%d"))
        avg_mood = sum(log['mood_score'] for log in recent_logs) / len(recent_logs) if recent_logs else 3
        
        if avg_mood < 3:
            suggestions.append("気分が低めです。小さなタスクから始めて勢いをつけましょう。")
        
        return {
            'suggestions': suggestions,
            'priorities': priorities,
            'overall_status': 'behind' if progress['overall_progress'] < 80 else 'on_track',
            'recommended_action': priorities[0]['action'] if priorities else "今日も着実に進めましょう！"
        }