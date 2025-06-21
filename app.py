import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
import json
from models import IncomeGoalManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_development")

# Initialize income goal manager
goal_manager = IncomeGoalManager()

@app.route("/")
def index():
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    
    # Get income sources and progress
    income_sources = goal_manager.get_income_sources()
    monthly_progress = goal_manager.get_monthly_progress()
    ai_suggestions = goal_manager.get_ai_suggestions()
    
    # Get today's logs
    today_logs = goal_manager.get_daily_logs(today_str)
    
    # Check for warnings
    warning = ""
    if not today_logs:
        if monthly_progress['overall_progress'] < 70:
            warning = f"⚠️ 今日のタスクがまだありません。目標まで{monthly_progress['missed_income']:,}円不足しています！"
        else:
            warning = "⚠️ 今日のタスクを記録しましょう。"
    
    return render_template("index.html",
                         today=today_str,
                         warning=warning,
                         income_sources=income_sources,
                         monthly_progress=monthly_progress,
                         ai_suggestions=ai_suggestions,
                         today_logs=today_logs)

@app.route("/add_log", methods=["POST"])
def add_log():
    try:
        source_id = int(request.form.get("source_id", 0))
        task_description = request.form.get("task_description", "").strip()
        units_completed = int(request.form.get("units_completed", 0))
        progress_percent = int(request.form.get("progress_percent", 0))
        mood_score = int(request.form.get("mood_score", 3))
        skip_reason = request.form.get("skip_reason", "").strip()
        
        if not task_description:
            flash("タスク内容を入力してください。", "error")
            return redirect(url_for("index"))
        
        if units_completed < 0:
            flash("完了数は0以上で入力してください。", "error")
            return redirect(url_for("index"))
        
        if progress_percent < 0 or progress_percent > 100:
            flash("進捗は0-100の範囲で入力してください。", "error")
            return redirect(url_for("index"))
        
        # Add daily log
        success = goal_manager.add_daily_log(source_id, task_description, units_completed, 
                                           progress_percent, mood_score, skip_reason)
        
        if success:
            flash("記録を追加しました！", "success")
        else:
            flash("記録の追加に失敗しました。", "error")
            
    except ValueError:
        flash("数値は正しい形式で入力してください。", "error")
    except Exception as e:
        logging.error(f"Error adding log: {e}")
        flash("エラーが発生しました。", "error")
    
    return redirect(url_for("index"))

@app.route("/income_sources")
def income_sources():
    sources = goal_manager.get_income_sources()
    monthly_progress = goal_manager.get_monthly_progress()
    
    return render_template("income_sources.html",
                         sources=sources,
                         monthly_progress=monthly_progress)

@app.route("/add_income_source", methods=["POST"])
def add_income_source():
    try:
        name = request.form.get("name", "").strip()
        unit_price = int(request.form.get("unit_price", 0))
        monthly_target = int(request.form.get("monthly_target", 0))
        description = request.form.get("description", "").strip()
        
        if not name:
            flash("収入源名を入力してください。", "error")
            return redirect(url_for("income_sources"))
        
        if unit_price <= 0 or monthly_target <= 0:
            flash("単価と月間目標は正の数で入力してください。", "error")
            return redirect(url_for("income_sources"))
        
        success = goal_manager.add_income_source(name, unit_price, monthly_target, description)
        
        if success:
            flash("収入源を追加しました！", "success")
        else:
            flash("収入源の追加に失敗しました。", "error")
            
    except ValueError:
        flash("数値は正しい形式で入力してください。", "error")
    except Exception as e:
        logging.error(f"Error adding income source: {e}")
        flash("エラーが発生しました。", "error")
    
    return redirect(url_for("income_sources"))

@app.route("/analytics")
def analytics_page():
    monthly_progress = goal_manager.get_monthly_progress()
    ai_suggestions = goal_manager.get_ai_suggestions()
    all_logs = goal_manager.get_daily_logs()
    
    return render_template("analytics.html",
                         monthly_progress=monthly_progress,
                         ai_suggestions=ai_suggestions,
                         all_logs=all_logs)

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        try:
            monthly_income_goal = int(request.form.get("monthly_income_goal", 70000))
            if monthly_income_goal < 1000:
                flash("月間収入目標は1000円以上で設定してください。", "error")
            else:
                goal_manager.update_settings({"monthly_income_goal": monthly_income_goal})
                flash("設定を更新しました！", "success")
        except ValueError:
            flash("月間収入目標は数値で入力してください。", "error")
        except Exception as e:
            logging.error(f"Error updating settings: {e}")
            flash("設定の更新に失敗しました。", "error")
        
        return redirect(url_for("settings"))
    
    current_settings = goal_manager.get_settings()
    return render_template("settings.html", settings=current_settings)

@app.route("/api/chart_data")
def chart_data():
    """API endpoint for chart data"""
    chart_type = request.args.get("type", "income_progress")
    
    if chart_type == "income_progress":
        monthly_progress = goal_manager.get_monthly_progress()
        
        # Create chart data for income progress
        labels = []
        actual_data = []
        target_data = []
        
        for source_id, progress in monthly_progress['source_progress'].items():
            labels.append(progress['name'])
            actual_data.append(progress['income_earned'])
            target_data.append(progress['target_income'])
        
        data = {
            'labels': labels,
            'datasets': [
                {
                    'label': '実際の収入',
                    'data': actual_data,
                    'backgroundColor': 'rgba(54, 162, 235, 0.6)',
                    'borderColor': 'rgba(54, 162, 235, 1)',
                    'borderWidth': 1
                },
                {
                    'label': '目標収入',
                    'data': target_data,
                    'backgroundColor': 'rgba(255, 99, 132, 0.6)',
                    'borderColor': 'rgba(255, 99, 132, 1)',
                    'borderWidth': 1
                }
            ]
        }
    else:
        data = {"error": "Invalid chart type"}
    
    return jsonify(data)

@app.route("/delete_income_source/<int:source_id>")
def delete_income_source(source_id):
    try:
        success = goal_manager.delete_income_source(source_id)
        if success:
            flash("収入源を削除しました。", "success")
        else:
            flash("収入源の削除に失敗しました。", "error")
    except Exception as e:
        logging.error(f"Error deleting income source: {e}")
        flash("エラーが発生しました。", "error")
    
    return redirect(url_for("income_sources"))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
