import csv
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

class DataManager:
    def __init__(self):
        self.log_file = "goal_tracking.csv"
        self.settings_file = "settings.json"
        self.init_files()
    
    def init_files(self):
        """Initialize CSV and settings files if they don't exist"""
        # Initialize CSV file
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["id", "date", "title", "progress", "feeling", "reason", "created_at"])
        
        # Initialize settings file
        if not os.path.exists(self.settings_file):
            default_settings = {
                "monthly_target": 30,
                "created_at": datetime.now().isoformat()
            }
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(default_settings, f, ensure_ascii=False, indent=2)
    
    def get_next_id(self) -> int:
        """Get the next available ID"""
        if not os.path.exists(self.log_file):
            return 1
        
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
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
    
    def add_entry(self, title: str, progress: int, feeling: str, reason: str) -> bool:
        """Add a new goal tracking entry"""
        try:
            entry_id = self.get_next_id()
            today = datetime.now().strftime("%Y-%m-%d")
            created_at = datetime.now().isoformat()
            
            with open(self.log_file, "a", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([entry_id, today, title, progress, feeling, reason, created_at])
            
            return True
        except Exception as e:
            print(f"Error adding entry: {e}")
            return False
    
    def get_entries_by_date(self, date_str: str) -> List[Dict[str, Any]]:
        """Get all entries for a specific date"""
        entries = []
        
        if not os.path.exists(self.log_file):
            return entries
        
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['date'] == date_str:
                        entry = {
                            'id': int(row['id']),
                            'date': row['date'],
                            'title': row['title'],
                            'progress': int(row['progress']),
                            'feeling': row['feeling'],
                            'reason': row['reason'],
                            'created_at': row.get('created_at', '')
                        }
                        entries.append(entry)
        except Exception as e:
            print(f"Error reading entries: {e}")
        
        return entries
    
    def get_all_entries(self) -> List[Dict[str, Any]]:
        """Get all entries"""
        entries = []
        
        if not os.path.exists(self.log_file):
            return entries
        
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        entry = {
                            'id': int(row['id']),
                            'date': row['date'],
                            'title': row['title'],
                            'progress': int(row['progress']),
                            'feeling': row['feeling'],
                            'reason': row['reason'],
                            'created_at': row.get('created_at', '')
                        }
                        entries.append(entry)
                    except (ValueError, KeyError) as e:
                        print(f"Error parsing entry: {e}")
                        continue
        except Exception as e:
            print(f"Error reading all entries: {e}")
        
        return entries
    
    def delete_entry(self, entry_id: int) -> bool:
        """Delete an entry by ID"""
        try:
            entries = self.get_all_entries()
            filtered_entries = [entry for entry in entries if entry['id'] != entry_id]
            
            # Rewrite the file
            with open(self.log_file, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["id", "date", "title", "progress", "feeling", "reason", "created_at"])
                
                for entry in filtered_entries:
                    writer.writerow([
                        entry['id'], entry['date'], entry['title'], 
                        entry['progress'], entry['feeling'], entry['reason'], 
                        entry['created_at']
                    ])
            
            return True
        except Exception as e:
            print(f"Error deleting entry: {e}")
            return False
    
    def get_settings(self) -> Dict[str, Any]:
        """Get application settings"""
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading settings: {e}")
            return {"monthly_target": 30}
    
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
    
    def get_entries_in_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get entries within a date range"""
        entries = self.get_all_entries()
        filtered_entries = []
        
        for entry in entries:
            if start_date <= entry['date'] <= end_date:
                filtered_entries.append(entry)
        
        return filtered_entries
