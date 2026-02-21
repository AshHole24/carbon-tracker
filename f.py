from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

# ===============================
# Emission Factors
# ===============================
ELECTRICITY_FACTOR = 0.82
LPG_FACTOR = 42.5
TRANSPORT_FACTOR = 0.2
WASTE_FACTOR = 1.8

# ===============================
# Database Setup
# ===============================
def init_db():
    conn = sqlite3.connect("carbon.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            household_name TEXT,
            electricity REAL,
            lpg REAL,
            transport REAL,
            waste REAL,
            total REAL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ===============================
# Home Route (Frontend)
# ===============================
@app.route("/")
def home():
    return render_template("demo1co2.html")

# ===============================
# Calculate API Route
# ===============================
@app.route("/calculate", methods=["POST"])
def calculate():
    data = request.get_json()

    electricity_kwh = float(data.get("electricity_kwh", 0))
    lpg_cylinders = float(data.get("lpg_cylinders", 0))
    distance_km = float(data.get("distance_km", 0))
    waste_kg = float(data.get("waste_kg", 0))
    recycle_pct = float(data.get("recycle_pct", 0))
    household_size = int(data.get("household_size", 1))

    if household_size <= 0:
        household_size = 1

    # Calculations
    electricity_co2 = electricity_kwh * ELECTRICITY_FACTOR
    lpg_co2 = lpg_cylinders * LPG_FACTOR
    transport_co2 = distance_km * TRANSPORT_FACTOR

    waste_raw = waste_kg * WASTE_FACTOR
    waste_co2 = waste_raw * (1 - recycle_pct / 100)

    total_monthly = electricity_co2 + lpg_co2 + transport_co2 + waste_co2

    # Save to database
    conn = sqlite3.connect("carbon.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO records (household_name, electricity, lpg, transport, waste, total)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data.get("household_name"),
        electricity_co2,
        lpg_co2,
        transport_co2,
        waste_co2,
        total_monthly
    ))
    conn.commit()
    conn.close()

    return jsonify({
        "electricity": round(electricity_co2, 2),
        "lpg": round(lpg_co2, 2),
        "transport": round(transport_co2, 2),
        "waste": round(waste_co2, 2),
        "total_monthly": round(total_monthly, 2)
    })

# ===============================
# Records Route (Styled Page)
# ===============================
@app.route("/records")
def records():
    conn = sqlite3.connect("carbon.db")
    c = conn.cursor()
    c.execute("SELECT * FROM records")
    data = c.fetchall()
    conn.close()
    return render_template("records.html", records=data)

# ===============================
# Run Server
# ===============================
if __name__ == "__main__":
    app.run()
