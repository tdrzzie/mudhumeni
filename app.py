from flask import Flask, request, g
from twilio.twiml.messaging_response import MessagingResponse
from handlers.commands import CommandHandler
import time
import sqlite3
import random
import datetime

# Prepare the instance of the Flask Application.
app = Flask(__name__)
command_handler = CommandHandler()

# Dictionary to store conversation histories
conversations = {}

SESSION_EXPIRATION_TIME = 10 * 60

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect("chatbot.db")
    return db


# Create tables for notifications, users, and assignments (if they don't exist)
def create_tables():
    with app.app_context():
        cursor = get_db().cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                phone_number TEXT NOT NULL UNIQUE,
                user_id TEXT NOT NULL UNIQUE,
                city TEXT,
                country TEXT
            )
        """)

        get_db().commit()


# Initialize the database
create_tables()

twilio_response = MessagingResponse()

# def generate_user_id():
#     # Generate a user ID prefixed with the current year and a random 3-digit number
#     current_year = str(datetime.datetime.now().year)
#     random_number = str(random.randint(100, 999))
#     random_letter = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
#     user_id = current_year + random_number + random_letter
#     return user_id

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

def create_user(phone_number, username, city, country):
    # Connect to the database
    db = get_db()
    cursor = db.cursor()

    # Check if user already exists
    cursor.execute("SELECT * FROM users WHERE phone_number = ?", (phone_number,))
    existing_user = cursor.fetchone()

    if not existing_user:
        # Generate a unique user ID
        # user_id = generate_user_id()
        user_id = phone_number

        # Insert user data into the database
        cursor.execute("""
            INSERT INTO users (username, phone_number, user_id, city, country)
            VALUES (?, ?, ?, ?, ?)
        """, (username, phone_number, user_id, city, country))
        db.commit()

        twilio_response.message("You are now registered!, You can now continue")
    else:
        return f"Hi {username}, it seems you are already registered. How can I assist you today?"

def update_conversation(user_id, message):
    current_time = time.time()
    if user_id in conversations:
        conversations[user_id]['history'].append(message)
        conversations[user_id]['last_active'] = current_time
    else:
        conversations[user_id] = {
            'history': [message],
            'last_active': current_time
        }

def get_conversation_history(user_id):
    if user_id in conversations:
        return "\n".join(conversations[user_id]['history'])
    return ""

def clear_expired_sessions():
    current_time = time.time()
    expired_users = [user_id for user_id, session in conversations.items()
                     if current_time - session['last_active'] > SESSION_EXPIRATION_TIME]
    for user_id in expired_users:
        del conversations[user_id]

@app.route('/bot', methods=['POST'])
def bot():
    
    try:
        # Clear expired sessions
        clear_expired_sessions()

        # Get the user's phone number to identify the session
        user_id = request.values.get('From', '')

        # Get the whole message that is send by the user.
        incoming_msg = request.values.get('Body', '')

        # Check if user exists
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE phone_number = ?", (user_id,))
        existing_user = cursor.fetchone()

        # Register user if not existing
        if not existing_user:
            resp.message("You are not registered! To get started, please enter your username, city, and country (separated by commas):")
            resp = MessagingResponse()
            msg = resp.message()
            msg.body(clean_response)

            if "," in incoming_msg:
                try:
                    details = incoming_msg.split(",")
                    username = details[0].strip()
                    city = details[1].strip()
                    country = details[2].strip()
                    phone_number = user_id
                    conn = get_db()
                    cursor = conn.cursor()

                    
                    try:
                        cursor.execute("INSERT INTO users (username, phone_number, user_id, city, country) VALUES (?, ?, ?, ?, ?)",
                                    (username, phone_number, user_id, city, country))
                        db.commit()
                        resp.message("Registration successful! Your user ID is: {}".format(user_id))
                    except sqlite3.IntegrityError:
                        resp.message("Phone number already registered.")
                    finally:
                        lastInput = ''
                        resp.message("You are not registered!")
                    
                    return str(resp)
                    
                    # update_conversation(user_id, welcome_message)
                except IndexError:  # Handle cases with missing details
                    resp.message("Invalid format. Please enter username, city, and country separated by commas (e.g., John Doe, Harare, Zimbabwe).")
                    return str(resp)
            
            # update_conversation(user_id, "Welcome! To get started, please enter your username, city, and country (separated by commas):")
            
        else:
            username = existing_user[1]  # Assuming username is the second column in the table

        # Update the conversation history
        update_conversation(user_id, f"User: {incoming_msg}")

        # Extract the first word.
        first_word = str(incoming_msg.split()[0]).lower()
        #hard coded gemini
        first_word = "gemini"

        username = existing_user[1]
        city = existing_user[4]
        country = existing_user[5]

        #bot identity hardcoded
        bot_identity = "Your name is Mudhumeni a friendly assistant for all things agriculture designed by Zimplugs to assist farmers. Your job is to assist clients. You are to reply 'Thanks for your message. While I can't answer questions unrelated to agriculture, you can find general information online or contact +263778669438 if you believe this question is related to agriculture' if the below question is not related to agriculture. "
        bot_identity += "If they greet you on their last message, you introduce yourself and tell them you are here to assist them on anything agriculture for example weather, climate, planting recommentations, forecasts, predictions and all that you can assist on agriculture. You are to answer the client if their question has something to do with agriculture. Under any circumstances you are not to tell the client that you are gemini. "
        bot_identity += "If client uses another language, you translate to their language and then respond in their language, If you fail to translate you respond 'Sorry I can only understand English for the momemnt'."
        bot_identity += "The user is {username} from {city}, {country}"
        bot_identity += "Now respond to the below below\n\n"

        # Get the conversation history
        conversation_history = get_conversation_history(user_id)

        # Message of the user.
        message = ' '.join(incoming_msg.split()[1:])

        # Combine the bot identity, conversation history, and the new message
        combined_message = f"{bot_identity}{conversation_history}\nUser: {message}\n"

        # Get the response.
        response = command_handler.handle_command(first_word, bot_identity+combined_message)

        # If the response starts with "Mudhumeni: ", remove this prefix for the user's response
        clean_response = response
        if response.startswith("Mudhumeni: "):
            clean_response = response[len("Mudhumeni: "):]

        # Update the conversation history with the bot's response
        update_conversation(user_id, f"Mudhumeni: {response}")


        # Prepare & return the response back to WhatsApp.
        resp = MessagingResponse()
        msg = resp.message()
        msg.body(clean_response)
        return str(resp)

    # Handle any errors.
    except Exception as e:
        print(f"An error occurred while processing the request: {e}")
        return str(MessagingResponse().message("Sorry, an error occurred while processing your request."))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')