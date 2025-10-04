import pyodbc
import bcrypt
import secrets
import uuid
from flask import Flask, request, render_template, session
from flask_session import Session


conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost\\SQLEXPRESS;'
    'DATABASE=model;'
    'Trusted_Connection=yes;'
)
cursor = conn.cursor()

logged_in = False

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = secrets.token_hex(32)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/createacc.html', methods=['post', 'get'])
def createacc():
    return render_template('createacc.html')

@app.route('/loginpage.html', methods=['post', 'get'])
def loginpage():
    return render_template('loginpage.html')

@app.route('/aboutus.html', methods=['post', 'get'])
def about_us():
    return render_template('aboutus.html')

@app.route('/chat.html', methods=['post', 'get'])
def chat():
    return render_template('chat.html')

@app.route('/chat_logged_in.html', methods=['post', 'get'])
def logged_in_chat():
    Uid = session.get('user_id')
    if not Uid:
        return render_template('chat_logged_in.html', logged_in=False, all_chats=[])

    cursor.execute(
        "SELECT DISTINCT Session_Id FROM ChatSessions WHERE UserId = ?",
        (Uid,)
    )
    session_rows = cursor.fetchall()
    session_id_list = [row[0] for row in session_rows]

    all_chats = []
    for ses_id in session_id_list:
        cursor.execute(
            "SELECT User_Chat, Bot_Chat FROM ChatSessions WHERE Session_Id = ? ORDER BY CreatedAt",
            (ses_id,)
        )
        messages = cursor.fetchall()
        session_messages = [[row[0], row[1]] for row in messages]
        all_chats.append(session_messages)

    return render_template('chat_logged_in.html', logged_in=True, all_chats=all_chats)

@app.route('/submit', methods=['POST', 'GET'])
def insert():
    if request.method == 'POST':
        user = request.form.get('name')
        password = request.form.get('password')
        confirmed = request.form.get('confirm')
        email = request.form.get('email')

        cursor.execute(
            "SELECT * FROM Users WHERE Email = ?;",(email,)
        )
        val = cursor.fetchone()
        if val:
            return render_template("index.html", message="An account with this email already exists.")
        else: 
            if password == confirmed:
                hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

                cursor.execute(
                    "INSERT INTO Users (person_name, Email, PasswordHash) VALUES (?, ?, ?)",
                    (user, email, hashed)
                )
                conn.commit()
                return render_template('logged_in_index.html', message="Account created successfully!")
            else: 
                return render_template('createacc.html', message="Password is incorrect, please try again")

@app.route('/login', methods=['POST', 'GET'])
def login():
    chat_sessions = str(uuid.uuid4())
    session['session_id'] = chat_sessions
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")
        cursor.execute("SELECT PasswordHash FROM Users WHERE Email = ?;", (email.strip(),))
        row = cursor.fetchone()
        if row:  
            stored_hash = row[0] 
            if isinstance(stored_hash, str):
                stored_hash = stored_hash.encode('utf-8')

            candidate_password = password.encode('utf-8')
            if bcrypt.checkpw(candidate_password, stored_hash):
                cursor.execute("SELECT person_name FROM Users WHERE Email = ?;", (email.strip(),))
                n = cursor.fetchone()
                n1 = n[0]
                if isinstance(n1, str):
                    logged_in = True
                    cursor.execute(
                        "SELECT UserID FROM Users WHERE Email = ?;", (email.strip(), )
                    )
                    uid = cursor.fetchone()
                    Uid = uid[0]
                    cursor.execute(
                        "INSERT INTO ChatSessions (UserId, Session_Id) VALUES (?, ?)", (Uid, chat_sessions)
                    )
                    session['user_id'] = Uid
                    conn.commit()
                    return render_template('logged_in_index.html', message="Logged in successfully!", name=n1, logged_in=logged_in)
                else: 
                    logged_in = True
                    cursor.execute(
                        "SELECT UserID FROM Users WHERE Email = ?;", (email.strip(), )
                    )
                    uid = cursor.fetchone()
                    Uid = uid[0]
                    cursor.execute(
                        "INSERT INTO ChatSessions (UserId, Session_Id) VALUES (?, ?)", (Uid, chat_sessions)
                    )
                    session['user_id'] = Uid
                    conn.commit()
                    return render_template('logged_in_index.html', message="Logged in successfully!", name="User", logged_in=logged_in)
            else:
                conn.commit()
                return render_template('loginpage.html', message="Incorrect password, please try again")
        else:
            conn.commit()
            return render_template('createacc.html', message="Account does not exist, please create an account")
        
@app.route("/save_message", methods=["POST"])
def save_message():
    if 'user_id' not in session:
        return {"status": "error", "message": "Not logged in"}, 401
    data = request.get_json()
    message = data.get("message")
    sender = data.get("sender")
    user_id = session['user_id']

    session_id = session.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
    cursor.execute(
        "SELECT User_Chat, Bot_Chat FROM ChatSessions WHERE UserId = ? AND Session_Id = ?",
        (user_id, session_id)
    )
    row = cursor.fetchone()

    if row:
        current_user_chat, current_bot_chat = row

        if sender == 'user':
            updated_user_chat = (current_user_chat or '') + ("\n" if current_user_chat else '') + message
            cursor.execute(
                "UPDATE ChatSessions SET User_Chat = ? WHERE UserId = ? AND Session_Id = ?",
                (updated_user_chat, user_id, session_id)
            )
        else:
            updated_bot_chat = (current_bot_chat or '') + ("\n" if current_bot_chat else '') + message
            cursor.execute(
                "UPDATE ChatSessions SET Bot_Chat = ? WHERE UserId = ? AND Session_Id = ?",
                (updated_bot_chat, user_id, session_id)
            )
    else:

        if sender == 'user':
            cursor.execute(
                "INSERT INTO ChatSessions (UserId, Session_Id, User_Chat) VALUES (?, ?, ?)",
                (user_id, session_id, message)
            )
        else:
            cursor.execute(
                "INSERT INTO ChatSessions (UserId, Session_Id, Bot_Chat) VALUES (?, ?, ?)",
                (user_id, session_id, message)
            )

    conn.commit()
    return {"status": "ok"}

@app.route("/get_chat_history")
def get_chat_history():
    Uid = session.get("user_id")
    if not Uid:
        return {"all_chats": []}

    cursor.execute(
        "SELECT DISTINCT Session_Id FROM ChatSessions WHERE UserId = ?", (Uid,)
    )
    session_rows = cursor.fetchall()
    session_id_list = [row[0] for row in session_rows]

    all_chats = []
    for ses_id in session_id_list:
        cursor.execute(
            "SELECT User_Chat, Bot_Chat FROM ChatSessions WHERE Session_Id = ? ORDER BY CreatedAt",
            (ses_id,)
        )
        messages = cursor.fetchall()
        session_messages = [[row[0], row[1]] for row in messages]
        all_chats.append(session_messages)

    return {"all_chats": all_chats}


@app.route("/logout.html", methods=["post", "get"])
def logout():
    session.clear()
    return render_template('index.html', message="Successfully logged out!")
 
if __name__ == "__main__":
    app.run(debug=True, ssl_context='adhoc')
