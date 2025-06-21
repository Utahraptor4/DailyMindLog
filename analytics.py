import calendar
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict, Counter
import math

class AnalyticsEngine:
    def __init__(self, data_manager):
        self.data_manager = data_manager
    
    def get_monthly_progress_stats(self) -> Dict[str, Any]:
        """Calculate monthly progress statistics"""
        today = datetime.now()
        month_start = today.replace(day=1)
        month_end = today.replace(day=calendar.monthrange(today.year, today.month)[1])
        
        start_str = month_start.strftime("%Y-%m-%d")
        end_str = month_end.strftime("%Y-%m-%d")
        
        entries = self.data_manager.get_entries_in_date_range(start_str, end_str)
        settings = self.data_manager.get_settings()
        monthly_target = settings.get('monthly_target', 30)
        
        # Calculate stats
        total_entries = len(entries)
        total_progress = sum(entry['progress'] for entry in entries)
        avg_progress = total_progress / total_entries if total_entries > 0 else 0
        
        # Days in month and current day
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        current_day = today.day
        
        # Calculate expected progress
        expected_daily_target = monthly_target / days_in_month
        expected_progress = expected_daily_target * current_day
        
        # Progress rate
        progress_rate = (total_entries / expected_progress * 100) if expected_progress > 0 else 0
        
        return {
            'total_entries': total_entries,
            'monthly_target': monthly_target,
            'progress_rate': round(progress_rate, 1),
            'avg_progress': round(avg_progress, 1),
            'days_completed': total_entries,
            'days_remaining': max(0, monthly_target - total_entries),
            'current_day': current_day,
            'days_in_month': days_in_month
        }
    
    def get_schedule_status(self) -> Dict[str, Any]:
        """Analyze schedule adherence"""
        today = datetime.now()
        month_start = today.replace(day=1)
        
        start_str = month_start.strftime("%Y-%m-%d")
        today_str = today.strftime("%Y-%m-%d")
        
        entries = self.data_manager.get_entries_in_date_range(start_str, today_str)
        settings = self.data_manager.get_settings()
        monthly_target = settings.get('monthly_target', 30)
        
        # Calculate expected vs actual
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        expected_daily_target = monthly_target / days_in_month
        expected_by_today = expected_daily_target * today.day
        actual_entries = len(entries)
        
        days_behind = max(0, math.ceil(expected_by_today - actual_entries))
        days_ahead = max(0, math.ceil(actual_entries - expected_by_today))
        
        # Status classification
        if days_behind > 2:
            status = "critical"
            status_text = "大幅遅れ"
        elif days_behind > 0:
            status = "behind"
            status_text = "遅れ気味"
        elif days_ahead > 1:
            status = "ahead"
            status_text = "順調"
        else:
            status = "on_track"
            status_text = "目標通り"
        
        return {
            'status': status,
            'status_text': status_text,
            'days_behind': days_behind,
            'days_ahead': days_ahead,
            'expected_by_today': round(expected_by_today, 1),
            'actual_entries': actual_entries
        }
    
    def get_weekly_trends(self) -> Dict[str, Any]:
        """Analyze weekly trends"""
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        
        weekly_data = []
        for i in range(4):  # Last 4 weeks
            start = week_start - timedelta(weeks=i)
            end = start + timedelta(days=6)
            
            start_str = start.strftime("%Y-%m-%d")
            end_str = end.strftime("%Y-%m-%d")
            
            entries = self.data_manager.get_entries_in_date_range(start_str, end_str)
            
            weekly_data.append({
                'week': f"Week {4-i}",
                'entries': len(entries),
                'avg_progress': sum(entry['progress'] for entry in entries) / len(entries) if entries else 0,
                'start_date': start_str,
                'end_date': end_str
            })
        
        return {'weekly_data': weekly_data}
    
    def get_mood_analysis(self) -> Dict[str, Any]:
        """Analyze mood patterns"""
        entries = self.data_manager.get_all_entries()
        
        mood_counts = Counter(entry['feeling'] for entry in entries if entry['feeling'])
        mood_progress = defaultdict(list)
        
        for entry in entries:
            if entry['feeling']:
                mood_progress[entry['feeling']].append(entry['progress'])
        
        mood_stats = {}
        for mood, progress_list in mood_progress.items():
            if progress_list:
                mood_stats[mood] = {
                    'count': len(progress_list),
                    'avg_progress': sum(progress_list) / len(progress_list),
                    'total_progress': sum(progress_list)
                }
        
        return {
            'mood_counts': dict(mood_counts),
            'mood_stats': mood_stats,
            'total_entries': len(entries)
        }
    
    def get_productivity_patterns(self) -> Dict[str, Any]:
        """Analyze productivity patterns"""
        entries = self.data_manager.get_all_entries()
        
        # Group by day of week
        weekday_data = defaultdict(list)
        for entry in entries:
            try:
                date_obj = datetime.strptime(entry['date'], "%Y-%m-%d")
                weekday = date_obj.strftime("%A")
                weekday_data[weekday].append(entry['progress'])
            except ValueError:
                continue
        
        weekday_stats = {}
        for day, progress_list in weekday_data.items():
            if progress_list:
                weekday_stats[day] = {
                    'count': len(progress_list),
                    'avg_progress': sum(progress_list) / len(progress_list),
                    'total_entries': len(progress_list)
                }
        
        # Find most productive days
        sorted_days = sorted(weekday_stats.items(), 
                           key=lambda x: x[1]['avg_progress'], reverse=True)
        
        return {
            'weekday_stats': weekday_stats,
            'most_productive_days': sorted_days[:3] if sorted_days else [],
            'least_productive_days': sorted_days[-3:] if len(sorted_days) >= 3 else []
        }
    
    def get_monthly_stats(self) -> Dict[str, Any]:
        """Get comprehensive monthly statistics"""
        today = datetime.now()
        
        # Current month
        current_month_start = today.replace(day=1)
        current_month_end = today.replace(day=calendar.monthrange(today.year, today.month)[1])
        
        # Previous month
        if today.month == 1:
            prev_month = today.replace(year=today.year-1, month=12, day=1)
        else:
            prev_month = today.replace(month=today.month-1, day=1)
        
        prev_month_end = prev_month.replace(day=calendar.monthrange(prev_month.year, prev_month.month)[1])
        
        # Get entries
        current_entries = self.data_manager.get_entries_in_date_range(
            current_month_start.strftime("%Y-%m-%d"),
            current_month_end.strftime("%Y-%m-%d")
        )
        
        prev_entries = self.data_manager.get_entries_in_date_range(
            prev_month.strftime("%Y-%m-%d"),
            prev_month_end.strftime("%Y-%m-%d")
        )
        
        # Calculate stats
        current_stats = {
            'total_entries': len(current_entries),
            'avg_progress': sum(entry['progress'] for entry in current_entries) / len(current_entries) if current_entries else 0,
            'total_progress': sum(entry['progress'] for entry in current_entries)
        }
        
        prev_stats = {
            'total_entries': len(prev_entries),
            'avg_progress': sum(entry['progress'] for entry in prev_entries) / len(prev_entries) if prev_entries else 0,
            'total_progress': sum(entry['progress'] for entry in prev_entries)
        }
        
        # Calculate changes
        entry_change = current_stats['total_entries'] - prev_stats['total_entries']
        progress_change = current_stats['avg_progress'] - prev_stats['avg_progress']
        
        return {
            'current_month': current_stats,
            'previous_month': prev_stats,
            'entry_change': entry_change,
            'progress_change': round(progress_change, 1),
            'month_name': today.strftime("%B %Y"),
            'prev_month_name': prev_month.strftime("%B %Y")
        }
    
    def get_monthly_progress_chart_data(self) -> Dict[str, Any]:
        """Get data for monthly progress chart"""
        today = datetime.now()
        month_start = today.replace(day=1)
        
        # Get daily data for current month
        daily_data = []
        labels = []
        
        for day in range(1, today.day + 1):
            date = month_start.replace(day=day)
            date_str = date.strftime("%Y-%m-%d")
            entries = self.data_manager.get_entries_by_date(date_str)
            
            daily_data.append(len(entries))
            labels.append(str(day))
        
        # Calculate target line
        settings = self.data_manager.get_settings()
        monthly_target = settings.get('monthly_target', 30)
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        daily_target = monthly_target / days_in_month
        
        target_line = [daily_target * (i + 1) for i in range(len(daily_data))]
        
        return {
            'labels': labels,
            'datasets': [
                {
                    'label': '実際の進捗',
                    'data': [sum(daily_data[:i+1]) for i in range(len(daily_data))],
                    'borderColor': 'rgb(54, 162, 235)',
                    'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                    'tension': 0.1
                },
                {
                    'label': '目標ライン',
                    'data': target_line,
                    'borderColor': 'rgb(255, 99, 132)',
                    'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                    'borderDash': [5, 5],
                    'tension': 0.1
                }
            ]
        }
    
    def get_weekly_trends_chart_data(self) -> Dict[str, Any]:
        """Get data for weekly trends chart"""
        weekly_trends = self.get_weekly_trends()
        
        labels = [week['week'] for week in weekly_trends['weekly_data']]
        entries_data = [week['entries'] for week in weekly_trends['weekly_data']]
        progress_data = [round(week['avg_progress'], 1) for week in weekly_trends['weekly_data']]
        
        return {
            'labels': labels,
            'datasets': [
                {
                    'label': 'エントリー数',
                    'data': entries_data,
                    'backgroundColor': 'rgba(75, 192, 192, 0.6)',
                    'borderColor': 'rgba(75, 192, 192, 1)',
                    'yAxisID': 'y'
                },
                {
                    'label': '平均進捗 (%)',
                    'data': progress_data,
                    'backgroundColor': 'rgba(153, 102, 255, 0.6)',
                    'borderColor': 'rgba(153, 102, 255, 1)',
                    'yAxisID': 'y1'
                }
            ]
        }
    
    def get_mood_distribution_chart_data(self) -> Dict[str, Any]:
        """Get data for mood distribution chart"""
        mood_analysis = self.get_mood_analysis()
        
        if not mood_analysis['mood_counts']:
            return {'labels': [], 'datasets': []}
        
        labels = list(mood_analysis['mood_counts'].keys())
        data = list(mood_analysis['mood_counts'].values())
        
        colors = [
            'rgba(255, 99, 132, 0.8)',
            'rgba(54, 162, 235, 0.8)',
            'rgba(255, 205, 86, 0.8)',
            'rgba(75, 192, 192, 0.8)',
            'rgba(153, 102, 255, 0.8)',
            'rgba(255, 159, 64, 0.8)'
        ]
        
        return {
            'labels': labels,
            'datasets': [{
                'data': data,
                'backgroundColor': colors[:len(labels)],
                'borderWidth': 2
            }]
        }
