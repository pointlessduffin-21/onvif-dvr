import sqlite3
import os
from datetime import datetime


def ensure_column(cursor, table, column, definition):
    """Ensure a column exists on the given table, adding it if missing"""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    if column not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

def get_db_connection():
    """Get database connection"""
    db_path = os.getenv('DATABASE_PATH', 'onvif_viewer.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with all required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Cameras table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cameras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            host TEXT NOT NULL,
            port INTEGER DEFAULT 80,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            manufacturer TEXT,
            model TEXT,
            firmware_version TEXT,
            serial_number TEXT,
            profiles_supported TEXT,
            status TEXT DEFAULT 'offline',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Camera profiles table (Profile S, G, C, A, T, M, D support)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS camera_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id INTEGER NOT NULL,
            profile_token TEXT NOT NULL,
            profile_name TEXT,
            profile_type TEXT,
            video_encoder_config TEXT,
            video_source_config TEXT,
            audio_encoder_config TEXT,
            ptz_config TEXT,
            metadata_config TEXT,
            analytics_config TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (camera_id) REFERENCES cameras (id) ON DELETE CASCADE
        )
    ''')
    
    # Video streams table (Profile S, T)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS video_streams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id INTEGER NOT NULL,
            profile_token TEXT NOT NULL,
            stream_uri TEXT NOT NULL,
            stream_type TEXT,
            protocol TEXT,
            resolution TEXT,
            framerate INTEGER,
            bitrate INTEGER,
            codec TEXT,
            channel_number INTEGER,
            stream_variant TEXT,
            stream_label TEXT,
            is_active BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (camera_id) REFERENCES cameras (id) ON DELETE CASCADE
        )
    ''')

    # Ensure newer columns exist when upgrading existing installations
    ensure_column(cursor, 'video_streams', 'channel_number', 'INTEGER')
    ensure_column(cursor, 'video_streams', 'stream_variant', 'TEXT')
    ensure_column(cursor, 'video_streams', 'stream_label', 'TEXT')
    
    # Recordings table (Profile G)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recordings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id INTEGER NOT NULL,
            recording_token TEXT,
            track_token TEXT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            recording_status TEXT,
            file_path TEXT,
            file_size INTEGER,
            duration INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (camera_id) REFERENCES cameras (id) ON DELETE CASCADE
        )
    ''')
    
    # Access control table (Profile C, A)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS access_control (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id INTEGER NOT NULL,
            access_point_token TEXT,
            access_point_name TEXT,
            access_point_type TEXT,
            capabilities TEXT,
            status TEXT,
            configuration TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (camera_id) REFERENCES cameras (id) ON DELETE CASCADE
        )
    ''')
    
    # Access control events table (Profile C, A)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS access_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id INTEGER NOT NULL,
            access_point_token TEXT,
            event_type TEXT,
            event_time TIMESTAMP,
            credential_token TEXT,
            decision TEXT,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (camera_id) REFERENCES cameras (id) ON DELETE CASCADE
        )
    ''')
    
    # Peripherals table (Profile D)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS peripherals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id INTEGER NOT NULL,
            peripheral_token TEXT,
            peripheral_type TEXT,
            peripheral_name TEXT,
            capabilities TEXT,
            status TEXT,
            configuration TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (camera_id) REFERENCES cameras (id) ON DELETE CASCADE
        )
    ''')
    
    # Events and metadata table (Profile M)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id INTEGER NOT NULL,
            event_topic TEXT,
            event_type TEXT,
            event_time TIMESTAMP,
            event_data TEXT,
            source TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (camera_id) REFERENCES cameras (id) ON DELETE CASCADE
        )
    ''')
    
    # Analytics configurations table (Profile M)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analytics_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id INTEGER NOT NULL,
            config_token TEXT,
            config_name TEXT,
            analytics_module TEXT,
            parameters TEXT,
            is_active BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (camera_id) REFERENCES cameras (id) ON DELETE CASCADE
        )
    ''')
    
    # PTZ presets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ptz_presets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id INTEGER NOT NULL,
            profile_token TEXT,
            preset_token TEXT,
            preset_name TEXT,
            pan_position REAL,
            tilt_position REAL,
            zoom_position REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (camera_id) REFERENCES cameras (id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == '__main__':
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
    init_db()
