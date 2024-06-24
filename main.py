from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import json
import os

json_file_path = os.path.join(os.path.dirname(__file__), "data.json")

app = Flask(__name__)
app.config["SECRET_KEY"] = "haha"
socketio = SocketIO(app)

# Load user and room data from JSON file
with open(json_file_path, "r") as file:
    data = json.load(file)


users = data["users"]
rooms = data["rooms"]

def decrypt_caesar(ciphertext, shift):
    plaintext = ""
    for char in ciphertext:
        if char.isalpha():  # Check if the character is an alphabet
            if char.isupper():  # For uppercase letters
                decrypted_char = chr((ord(char) - 65 - shift) % 26 + 65)
            else:  # For lowercase letters
                decrypted_char = chr((ord(char) - 97 - shift) % 26 + 97)
        else:  # For non-alphabetic characters
            decrypted_char = char
        plaintext += decrypted_char
    return plaintext

@app.route("/")
def index():
    return render_template('login.html')

@app.route("/login", methods=["POST"])
def login():
    password = request.form['password']
    name = request.form.get('name')

    for user, info in users.items():
        if info["username"] == name and info["password"] == password:
            session['name'] = user
            return redirect(url_for('home'))

    return render_template('login.html')

@app.route("/home", methods=["POST", "GET"])
def home():
    name = session.get("name")
    if name is None:
        return redirect(url_for('index'))

    if request.method == "POST":
        selected_room = request.form.get("room")
        if selected_room not in rooms:
            return render_template("home.html", error="Invalid room code.", rooms=rooms, name=name)
        
        session["room"] = selected_room
        return redirect(url_for("room"))

    return render_template("home.html", rooms=rooms, name=name)

@app.route("/room")
def room():
    if 'name' not in session:
        return redirect(url_for('index'))

    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", code=room, messages=rooms[room]["messages"])

@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return 
    
    # Decrypt the message using Caesar Cipher decryption
    decrypted_message = decrypt_caesar(data["data"], 3)
    
    content = {
        "name": session.get("name"),
        "message": decrypted_message
    }
    original = {
        "name": session.get("name"),
        "message": data["data"]
    }

    print(original)

    # Save the decrypted message to the JSON file
    rooms[room]["messages"].append(content)
    save_data()

    # Send the encrypted message back to the client
    send({"name": session.get("name"), "message": data["data"]}, to=room)


@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name: 
        return
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({"name": name, "message": "has entered the room", "without_encryption": True}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            rooms[room]["members"] = 0
    
    send({"name": name, "message": "has left the room", "without_encryption": True}, to=room)
    print(f"{name} has left the room {room}")


def save_message_to_json(message_content):
    room = session.get("room")
    if room not in rooms:
        return

    rooms[room]["messages"].append(message_content)
    save_data()

# Function to save updated data to JSON file.
def save_data():
    with open(json_file_path, "w") as file:
        json.dump(data, file)

if __name__ == "__main__":
    socketio.run(app, debug=True)