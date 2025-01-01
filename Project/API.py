from flask import Flask, request, jsonify


from datetime import datetime
import sqlite3
from flask_cors import CORS


app = Flask(__name__)
CORS(app)


# Database path
DATABASE = "temperature_data.db"


def init_db():
    """Initialize the database."""
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS sensor_data (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            device_id TEXT NOT NULL,
                            timestamp TEXT,
                            temperature REAL NOT NULL,
                            movement TEXT,
                            humidity REAL NOT NULL
                        )''')


@app.route('/api/send-data', methods=['POST', 'OPTIONS'])
def send_data():
    """Receive temperature and humidity data."""
    if request.method == 'OPTIONS':
        return '', 200
       
    try:
        data = request.get_json()
        if not data or 'device_id' not in data or 'temperature' not in data or 'humidity' not in data or 'timestamp' not in data or 'movement' not in data:
            return jsonify({"error": "Invalid data"}), 400


        # Save data to the database
        with sqlite3.connect(DATABASE) as conn:
            conn.execute("INSERT INTO sensor_data (device_id, timestamp, temperature, movement, humidity) VALUES (?, ?, ?, ?, ?)",
                         (data['device_id'], data['timestamp'], data['temperature'], data['movement'], data['humidity']))
        return jsonify({"message": "Data saved successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/read-data', methods=['GET'])
def read_data():
    """Retrieve all temperature and humidity data."""
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sensor_data")
            records = cursor.fetchall()
        if not records:
            return jsonify({"message": "No data available"}), 404
        return jsonify([
            {"id": row[0], "device_id": row[1], "timestamp": row[2], "temperature": row[3], "movement": row[4], "humidity": row[5]}
            for row in records
        ]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/clean-db', methods=['GET'])
def clean_db():
    """Clean all data from the database."""
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sensor_data")
            if cursor.rowcount > 0:
                return jsonify({"message": f"Successfully deleted {cursor.rowcount} records"}), 200
            return jsonify({"message": "Database is already empty"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
