import random
from datetime import datetime, timedelta
from typing import Dict, List, Any

class MotivationalCoach:
    def __init__(self, data_manager):
        self.data_manager = data_manager
        
        # Motivational messages by mood/situation
        self.messages = {
            'default': [
                "今日も一歩ずつ前進しましょう！🌟",
                "継続は力なり。今日も頑張りましょう！💪",
                "小さな積み重ねが大きな成果を生みます✨",
                "今日という日は二度と来ません。大切にしましょう🌸"
            ],
            'behind_schedule': [
                "遅れていても大丈夫！今から始めれば追いつけます🚀",
                "完璧でなくても前進することが大切です🌈",
                "今日からリセット！新しいスタートを切りましょう⭐",
                "小さな一歩でも前進は前進です👣"
            ],
            'on_track': [
                "素晴らしいペースです！この調子で続けましょう🎉",
                "順調な進歩ですね！継続の力を感じています💫",
                "目標に向かって着実に歩んでいますね🎯",
                "この勢いを保って、さらに高みを目指しましょう🏔️"
            ],
            'ahead_of_schedule': [
                "驚異的なペースです！素晴らしい努力ですね🏆",
                "目標を上回る成果、本当に立派です👑",
                "この調子なら大きな目標も達成できそうですね🌟",
                "自分自身を誇りに思ってください🎖️"
            ],
            'mood_based': {
                '元気': [
                    "その元気さが成功の秘訣ですね！🌞",
                    "エネルギッシュな姿勢、素晴らしいです⚡",
                    "元気いっぱいで今日も頑張りましょう🔥"
                ],
                '普通': [
                    "普通の日でも着実に進歩していますね📈",
                    "コンスタントな努力が一番大切です🎯",
                    "淡々と続けることの価値を知っていますね💎"
                ],
                '疲れ': [
                    "疲れていても継続する姿勢、立派です🌙",
                    "休息も成長の一部です。無理しないでくださいね☁️",
                    "疲れた時こそ自分を労わってあげましょう🛁"
                ],
                'やる気': [
                    "そのやる気が成功への鍵です🔑",
                    "モチベーションの高さが伝わってきます🚀",
                    "やる気に満ちた姿勢、とても素敵です✨"
                ],
                '集中': [
                    "集中力の高さが成果に繋がっていますね🎯",
                    "フォーカスした取り組み、素晴らしいです🔍",
                    "集中して取り組む姿勢が光っています💡"
                ]
            }
        }
        
        # Task suggestions based on situation
        self.task_suggestions = {
            'behind_schedule': [
                "短時間でできるタスクから始めてみましょう",
                "今日は軽めの作業で感覚を取り戻しましょう",
                "15分だけでも取り組んでみませんか？",
                "小さな目標を設定して達成感を味わいましょう"
            ],
            'normal': [
                "いつも通りのペースで取り組みましょう",
                "今日の目標を明確にして開始しましょう",
                "集中できる環境を整えて始めませんか？",
                "計画的に進めていきましょう"
            ],
            'ahead': [
                "余裕があるので新しいことに挑戦してみませんか？",
                "高い目標を設定してチャレンジしましょう",
                "より質の高い成果を目指してみましょう",
                "追加のタスクにも取り組んでみませんか？"
            ]
        }
    
    def get_daily_motivation(self) -> Dict[str, Any]:
        """Get daily motivational message based on current situation"""
        # Analyze current situation
        schedule_status = self._get_schedule_status()
        recent_mood = self._get_recent_mood()
        
        # Select appropriate message
        if schedule_status == 'behind':
            messages = self.messages['behind_schedule']
        elif schedule_status == 'ahead':
            messages = self.messages['ahead_of_schedule']
        elif schedule_status == 'on_track':
            messages = self.messages['on_track']
        else:
            messages = self.messages['default']
        
        # Add mood-based message if available
        mood_message = ""
        if recent_mood and recent_mood in self.messages['mood_based']:
            mood_message = random.choice(self.messages['mood_based'][recent_mood])
        
        main_message = random.choice(messages)
        
        return {
            'main_message': main_message,
            'mood_message': mood_message,
            'motivation_type': schedule_status,
            'recent_mood': recent_mood
        }
    
    def get_task_suggestions(self) -> List[str]:
        """Get task suggestions based on current schedule status"""
        schedule_status = self._get_schedule_status()
        
        if schedule_status == 'behind':
            suggestions = self.task_suggestions['behind_schedule']
        elif schedule_status == 'ahead':
            suggestions = self.task_suggestions['ahead']
        else:
            suggestions = self.task_suggestions['normal']
        
        # Return 2-3 random suggestions
        return random.sample(suggestions, min(3, len(suggestions)))
    
    def get_personalized_encouragement(self, reason: str, mood: str) -> str:
        """Generate personalized encouragement based on reason and mood"""
        encouragement_templates = {
            'time_constraint': [
                "時間が限られていても、{mood}な気持ちで取り組めたのは素晴らしいです！",
                "忙しい中でも続ける意志の強さを感じます。{mood}な姿勢が素敵ですね。"
            ],
            'motivation_low': [
                "モチベーションが低い時でも継続するのは本当に立派です。",
                "やる気が出ない日こそ、真の成長があります。"
            ],
            'feeling_good': [
                "{mood}な気持ちで取り組めて良かったですね！",
                "その{mood}な姿勢が成功への道のりを照らしています。"
            ],
            'default': [
                "継続する姿勢、本当に素晴らしいです！",
                "一歩一歩の積み重ねが大きな成果に繋がります。"
            ]
        }
        
        # Simple keyword matching for reason analysis
        reason_lower = reason.lower()
        if any(word in reason_lower for word in ['時間', '忙しい', '急いで']):
            templates = encouragement_templates['time_constraint']
        elif any(word in reason_lower for word in ['やる気', 'モチベーション', '気分']):
            templates = encouragement_templates['motivation_low']
        elif any(word in reason_lower for word in ['良い', '楽しい', '充実']):
            templates = encouragement_templates['feeling_good']
        else:
            templates = encouragement_templates['default']
        
        template = random.choice(templates)
        return template.format(mood=mood)
    
    def _get_schedule_status(self) -> str:
        """Get current schedule status (private method)"""
        from analytics import AnalyticsEngine
        analytics = AnalyticsEngine(self.data_manager)
        schedule_status = analytics.get_schedule_status()
        
        days_behind = schedule_status.get('days_behind', 0)
        days_ahead = schedule_status.get('days_ahead', 0)
        
        if days_behind > 1:
            return 'behind'
        elif days_ahead > 1:
            return 'ahead'
        else:
            return 'on_track'
    
    def _get_recent_mood(self) -> str:
        """Get most recent mood from entries"""
        today = datetime.now().strftime("%Y-%m-%d")
        recent_entries = self.data_manager.get_entries_by_date(today)
        
        if recent_entries:
            # Get the most recent entry's mood
            latest_entry = max(recent_entries, key=lambda x: x.get('created_at', ''))
            return latest_entry.get('feeling', '')
        
        # Get mood from yesterday if no today entries
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_entries = self.data_manager.get_entries_by_date(yesterday)
        
        if yesterday_entries:
            latest_entry = max(yesterday_entries, key=lambda x: x.get('created_at', ''))
            return latest_entry.get('feeling', '')
        
        return ''
    
    def get_weekly_motivation_summary(self) -> Dict[str, Any]:
        """Get weekly motivation summary and achievements"""
        from analytics import AnalyticsEngine
        analytics = AnalyticsEngine(self.data_manager)
        
        weekly_trends = analytics.get_weekly_trends()
        current_week = weekly_trends['weekly_data'][0] if weekly_trends['weekly_data'] else {}
        
        achievements = []
        challenges = []
        
        # Analyze weekly performance
        if current_week.get('entries', 0) >= 5:
            achievements.append("今週は5日以上活動しました！素晴らしい継続力です🏆")
        
        if current_week.get('avg_progress', 0) >= 80:
            achievements.append("今週の平均進捗率が80%以上！高いパフォーマンスです⭐")
        
        if current_week.get('entries', 0) < 3:
            challenges.append("今週の活動日数が少なめです。明日から挽回しましょう💪")
        
        if current_week.get('avg_progress', 0) < 50:
            challenges.append("今週は進捗率が低めでした。来週はより集中して取り組みましょう🎯")
        
        return {
            'achievements': achievements,
            'challenges': challenges,
            'weekly_summary': f"今週は{current_week.get('entries', 0)}日活動し、平均進捗率{current_week.get('avg_progress', 0):.1f}%でした"
        }
