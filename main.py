from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
 


app = Flask(__name__)
app.config["SECRET_KEY"] = "haha"
socketio = SocketIO(app)

# This creates predefined rooms in this case 3 predefined rooms
# later, within the program, it will call back to this dictionary 
# and Identify which of the 3 rooms are trying to be connected to.

users = {
    "Mosiah":{"username": "mo", "password": "pass1"},
    "Audra":{"username": "au", "password": "pass2"}
}

rooms = {
    "ROOM1": {"members": 0, "messages": []},  
    "ROOM2": {"members": 0, "messages": []},
    "ROOM3": {"members": 0, "messages": []}
}

@app.route("/")
def index(): # This just Opens up the website main page which is the login page.
    return render_template('login.html')

# the login page logic, Collects the name to be used for identifying the person
# Checks to see if the password is equal to the predefined password, then 
# allows access to the homepage if the Password is correct.
@app.route("/login", methods=["POST"])
def login():

    password = request.form['password']
    name = request.form.get('name')  # Get the name from the form

    for user, info in users.items():
        if info["username"] == name and info["password"] == password:
            session['name'] = user  # Set the name in the session
            return redirect(url_for('home')) #takes you to home page

    return render_template('login.html') # takes you back to the login
            


    #if password == "pass": # check to see if the input in password is equal to pass
        #session['name'] = name  # Set the name in the session
        #return redirect(url_for('home')) #takes you to home page
    #else:
        #return render_template('login.html') # takes you back to the login

# After you select the room, you want to enter the homepage redirects
# you to the room you're supposed to go to.
@app.route("/home", methods=["POST", "GET"])
def home():

    name = session.get("name")  # Get the name from the session

    if name is None:  # If the name is not saved in the session, redirect to login
        return redirect(url_for('index'))

    if request.method == "POST": #the following only runs if POST is done in the HTML
        selected_room = request.form.get("room")# identifies which room was Selected.

        if selected_room not in rooms: # Checkes to see if the room Exist.
            return render_template("home.html", error="Invalid room code.", rooms=rooms, name=name)
        
        session["room"] = selected_room
        return redirect(url_for("room"))#Sends the user to the Select a room.

    return render_template("home.html", rooms=rooms, name=name)

@app.route("/room")
def room():
    if 'name' not in session: # Checks to make sure the user has a name.
        return redirect(url_for('index'))

    room = session.get("room") #this Checks if the room exists, and if not send you back to the homepage.
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", code=room, messages=rooms[room]["messages"])

@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms: #Checks to see if the room your in a real
        return 
    
    content = { #stats the varabuls for the messege the name, and the data/messege
        "name": session.get("name"),
        "message": data["data"]
    }

    send(content, to=room) # sends the content to the chat room
    rooms[room]["messages"].append(content) #adds the message to the list of messages
    print(f"{session.get('name')} said: {data['data']}")#to see in the turmenal

@socketio.on("connect")
def connect(auth):
    room = session.get("room") #finds room
    name = session.get("name") #finds name
    if not room or not name: 
        return
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room) # when you join the room, the message that you join the room you sent.
    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1 #ads and keeps track of the number of people in the room.
    print(f"{name} joined room {room}") # to see in the terminal

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms: # notifies, if someone's left the chat, and ends if no one's in it.
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    
    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} has left the room {room}")

if __name__ == "__main__":
    socketio.run(app, debug=True)

# notes on things to add
#-work on some form of encryption.
#-have the messages save on the chat.
#-add the Ability to scroll within the message div.