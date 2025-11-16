import psycopg2
import bcrypt
import secrets
import uuid
import requests
from flask import Flask, request, render_template, session, jsonify
from flask_session import Session
import os

# -----------------------------------------
# DATABASE SETUP
# -----------------------------------------
conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=os.getenv("DB_PORT")
)
cursor = conn.cursor()

# FIXED DATABASE SCHEMA (SAFE TO RUN MULTIPLE TIMES)
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    userid SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    passwordhash VARCHAR(255) NOT NULL,
    createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    person_name VARCHAR(255)
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    userid INT NOT NULL,
    session_id UUID NOT NULL,
    session_title VARCHAR(255),
    user_chat TEXT,
    bot_chat TEXT,
    createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (userid) REFERENCES users(userid) ON DELETE CASCADE
);
""")

conn.commit()

# -----------------------------------------
# FLASK SETUP
# -----------------------------------------
app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = secrets.token_hex(32)
Session(app)

RASA_URL = os.getenv("RASA_URL", "http://localhost:5005/webhooks/rest/webhook")

# -----------------------------------------
# ROUTES
# -----------------------------------------
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/createacc.html')
def createacc():
    return render_template('createacc.html')


@app.route('/loginpage.html')
def loginpage():
    return render_template('loginpage.html')


@app.route('/aboutus.html')
def about_us():
    return render_template('aboutus.html')


@app.route('/chat.html')
def chat_page():
    return render_template('chat.html')


# -----------------------------------------
# CHAT (NOT LOGGED IN)
# -----------------------------------------
@app.route("/chat", methods=["POST"])
def chat_api():
    user_message = request.json.get("message")

    try:
        response = requests.post(RASA_URL, json={"sender": "guest", "message": user_message})
        bot_messages = response.json()
        return jsonify(bot_messages)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------------------
# ACCOUNT CREATION
# -----------------------------------------
@app.route('/submit', methods=['POST'])
def insert():
    user = request.form.get('name')
    password = request.form.get('password')
    confirmed = request.form.get('confirm')
    email = request.form.get('email')

    cursor.execute("SELECT 1 FROM users WHERE email = %s", (email,))
    if cursor.fetchone():
        return render_template("index.html", message="Account already exists.")

    if password != confirmed:
        return render_template("createacc.html", message="Passwords do not match.")

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    cursor.execute(
        "INSERT INTO users (person_name, email, passwordhash) VALUES (%s, %s, %s)",
        (user, email, hashed)
    )
    conn.commit()

    return render_template("logged_in_index.html", message="Account created!")


# -----------------------------------------
# LOGIN
# -----------------------------------------
@app.route('/login', methods=['POST'])
def login():
    email = request.form.get("email")
    password = request.form.get("password")

    cursor.execute("SELECT userid, passwordhash, person_name FROM users WHERE email=%s", (email,))
    row = cursor.fetchone()

    if not row:
        return render_template("createacc.html", message="Account does not exist.")

    userid, stored_hash, name = row

    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode('utf-8')

    if not bcrypt.checkpw(password.encode('utf-8'), stored_hash):
        return render_template("loginpage.html", message="Incorrect password.")

    session_id = uuid.uuid4()
    session['user_id'] = userid
    session['session_id'] = str(session_id)

    cursor.execute(
        "INSERT INTO chat_sessions (userid, session_id) VALUES (%s, %s)",
        (userid, session_id)
    )
    conn.commit()

    return render_template("logged_in_index.html", name=name or "User")


# -----------------------------------------
# LOGGED-IN CHAT
# -----------------------------------------
@app.route("/chat_logged_in", methods=["POST"])
def chat_logged_in_api():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 403

    userid = session['user_id']
    session_id = session['session_id']
    message = request.json.get("message")

    # send to rasa
    response = requests.post(RASA_URL, json={"sender": str(userid), "message": message})
    bot_messages = response.json()

    bot_reply = bot_messages[0].get("text", "") if bot_messages else ""

    cursor.execute(
        "INSERT INTO chat_sessions (userid, session_id, user_chat, bot_chat) VALUES (%s, %s, %s, %s)",
        (userid, session_id, message, bot_reply)
    )
    conn.commit()

    return jsonify(bot_messages)


# -----------------------------------------
# CHAT HISTORY
# -----------------------------------------
@app.route("/get_chat_history")
def get_chat_history():
    if "user_id" not in session:
        return {"all_chats": []}

    userid = session["user_id"]

    cursor.execute("SELECT session_id FROM chat_sessions WHERE userid=%s GROUP BY session_id", (userid,))
    session_ids = cursor.fetchall()

    all_chats = []

    for (sid,) in session_ids:
        cursor.execute(
            "SELECT user_chat, bot_chat FROM chat_sessions WHERE session_id=%s ORDER BY createdat",
            (sid,)
        )
        messages = cursor.fetchall()
        all_chats.append([[u, b] for (u, b) in messages])

    return {"all_chats": all_chats}


# -----------------------------------------
# LOGOUT
# -----------------------------------------
@app.route("/logout.html")
def logout():
    session.clear()
    return render_template("index.html", message="Logged out!")


# -----------------------------------------
# RUN
# -----------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Flask running on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
