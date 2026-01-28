import sqlite3
from datetime import datetime
import threading


class GameDatabase:
    def __init__(self, db_name="game_save.db"):
        self.db_name = db_name
        self.lock = threading.Lock()
        self.init_database()
    
    def init_database(self):
        with self.lock:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS game_saves (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_name TEXT NOT NULL,
                    level INTEGER DEFAULT 1,
                    rubless INTEGER DEFAULT 0,
                    score INTEGER DEFAULT 0,
                    lives INTEGER DEFAULT 3,
                    save_date TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS level_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_name TEXT NOT NULL,
                    level INTEGER NOT NULL,
                    rubles_collected INTEGER DEFAULT 0,
                    pmcs_defeated INTEGER DEFAULT 0,
                    completion_time FLOAT,
                    score INTEGER DEFAULT 0,
                    completed BOOLEAN DEFAULT FALSE,
                    play_date TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS high_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_name TEXT NOT NULL,
                    total_score INTEGER DEFAULT 0,
                    total_rubless INTEGER DEFAULT 0,
                    levels_completed INTEGER DEFAULT 0,
                    record_date TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
    
    def save_game(self, player_name, level, rubless, score, lives):
        with self.lock:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM game_saves WHERE player_name = ?", (player_name,))
            
            cursor.execute('''
                INSERT INTO game_saves (player_name, level, rubless, score, lives, save_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (player_name, level, rubless, score, lives, datetime.now()))
            
            conn.commit()
            conn.close()
    
    def load_game(self, player_name):
        with self.lock:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT level, rubless, score, lives FROM game_saves 
                WHERE player_name = ? ORDER BY save_date DESC LIMIT 1
            ''', (player_name,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'level': result[0],
                    'rubless': result[1],
                    'score': result[2],
                    'lives': result[3]
                }
            return None
    
    def save_level_result(self, player_name, level, rubles_collected, pmcs_defeated, completion_time, score, completed=True):
        with self.lock:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO level_results 
                (player_name, level, rubles_collected, pmcs_defeated, completion_time, score, completed, play_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (player_name, level, rubles_collected, pmcs_defeated, completion_time, score, completed, datetime.now()))
            
            self._update_high_scores(conn, cursor, player_name, score, rubles_collected)
            
            conn.commit()
            conn.close()
    
    def _update_high_scores(self, conn, cursor, player_name, score, rubless):
        cursor.execute('''
            SELECT total_score, total_rubless, levels_completed 
            FROM high_scores WHERE player_name = ?
        ''', (player_name,))
        
        result = cursor.fetchone()
        
        if result:
            new_score = result[0] + score
            new_rubless = result[1] + rubless
            new_levels = result[2] + 1
            
            cursor.execute('''
                UPDATE high_scores 
                SET total_score = ?, total_rubless = ?, levels_completed = ?, record_date = ?
                WHERE player_name = ?
            ''', (new_score, new_rubless, new_levels, datetime.now(), player_name))
        else:
            cursor.execute('''
                INSERT INTO high_scores (player_name, total_score, total_rubless, levels_completed, record_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (player_name, score, rubless, 1, datetime.now()))
    
    def get_level_stats(self, level):
        with self.lock:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    AVG(rubles_collected) as avg_rubles,
                    AVG(completion_time) as avg_time,
                    COUNT(*) as play_count,
                    SUM(CASE WHEN completed THEN 1 ELSE 0 END) as completed_count
                FROM level_results 
                WHERE level = ?
            ''', (level,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[2] > 0:
                return {
                    'avg_rubles': result[0] or 0,
                    'avg_time': result[1] or 0,
                    'play_count': result[2],
                    'completion_rate': (result[3] / result[2]) * 100 if result[2] > 0 else 0
                }
            return None
    
    def get_high_scores(self, limit=10):
        with self.lock:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT player_name, total_score, total_rubless, levels_completed 
                FROM high_scores 
                ORDER BY total_score DESC 
                LIMIT ?
            ''', (limit,))
            
            results = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'player_name': r[0],
                    'total_score': r[1],
                    'total_rubless': r[2],
                    'levels_completed': r[3]
                }
                for r in results
            ]
    
    # def close_all_connections(self):
    #     with self.lock:
    #         pass