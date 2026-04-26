import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "packets.db")

def init_db():
    """Initializes the database and creates the packets table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS packets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            src_ip TEXT,
            dst_ip TEXT,
            src_port INTEGER,
            dst_port INTEGER,
            protocol TEXT,
            size INTEGER,
            timestamp REAL,
            is_local INTEGER
        )
    ''')
    conn.commit()
    conn.close()
    print(f"[*] Database initialized at {DB_PATH}")

def save_packets_batch(packet_list):
    """Saves a batch of packets to the database for efficiency."""
    if not packet_list:
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Convert dictionaries to tuples for batch insertion
    data = [
        (p['src_ip'], p['dst_ip'], p['src_port'], p['dst_port'], 
         p['protocol'], p['size'], p['timestamp'], int(p['is_local']))
        for p in packet_list
    ]
    
    cursor.executemany('''
        INSERT INTO packets (src_ip, dst_ip, src_port, dst_port, protocol, size, timestamp, is_local)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()