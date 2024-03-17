from flask import Flask, Blueprint, request, jsonify, render_template, session, redirect, url_for, abort 
from openai import OpenAI 
import os
import argparse

from parsers import parser_gpt, parser_sql
from pg_chat import connect, grab_chat, new_chat, append_message, recreate_loremaster_dialogue
from pg_users import hash_password 
from main import yggy_step

from chatter import Chatter 

HOST = 'localhost'
PORT = '5432'
USER = 'crossland'
PASSWORD = 'pass'
DATABASE = 'yggdrasil'

def make_parser():
    parser = argparse.ArgumentParser(description='Start our Yggy API')

    parser = parser_gpt(parser)
    parser = parser_sql(parser)

    return(parser)

parser = make_parser()
args= parser.parse_args()

app = Flask(__name__)

chat_blueprint = Blueprint('chat', __name__)
@chat_blueprint.route('/chat', methods=['GET'])
def chat():
    prompt = request.args.get('prompt')
    
    model = 'gpt-3.5-turbo'
    try:
        model = request.args.get('model')
    except:
        pass 

    # Call the OpenAI API with the prompt and get the response
    # Implement your logic here
    try:
        messages = [{'role':'user', 'content':prompt}]

        client = OpenAI(api_key=os.getenv("OPENAI_AUTH"))
        response = client.chat.completions.create(
            messages = messages,
            model = model
        )
        
        return({'response':response.choices[-1].message.content})
    except Exception as e:  
        return({'error':101, 'message':str(e)})
    

noting_blueprint = Blueprint('noting', __name__)
@noting_blueprint.route('/noting', methods=['GET'])
def noting():
    prompt = request.args.get('prompt')
    model = request.args.get('model')
    user = request.args.get('user')
    password = request.args.get('password')

    print("Connecting to database...")
    connection = connect(HOST, PORT, user, password, DATABASE)

    if(not connection):
        return({'error':101, 'message':'Could not connect to database'})

    nvector = request.args.get('nvector')
    if(not nvector):    
        nvector = 10

    embedder = request.args.get('embedder')
    if(not embedder):
        embedder = 'text-embedding-ada-002'

    model = request.args.get('model')
    if(not model):
        model='gpt-3.5-turbo-1106'

    chat_id = request.args.get('chat_id')
    if(not chat_id):
        try:
            chat_id = start_chat(connection, prompt, role='user')
            messages = [] 
        except Exception as e:
            return({'error':101, 'message':str(e)})
    else:
        try:
            messages = grab_chat(connection, chat_id)
        except Exception as e: 
            return({'error':102, 'message':str(e)})

    print("Building Chatter...")
    chatter = Chatter(model)
    try:
        print("Asking IGOR...")
        igor_reply = ask_igor(prompt, embedder, model, nvector, chatter=chatter, verbose=True)
    except Exception as e: 
        return({'error':103, 'message':str(e)})

    try:
        print("Asking LORE MASTER...")
        loremaster_reply, messages = ask_loremaster(prompt, igor_reply, chatter, messages=messages, verbose=True)
    except Exception as e:
        print(e)
        return({'error':104, 'message':str(e)})

    append_message(connection, chat_id, messages[-1]['content'], role='user')
    append_message(connection, chat_id, loremaster_reply, role='assistant')
    return({'response':loremaster_reply})


yggy_blueprint = Blueprint('yggy', __name__)
@yggy_blueprint.route('/yggy', methods=['POST'])
def yggy():
    try:
        data = request.args 
    except Exception as e:
        print(e)
        return({'error':100, 'message':'Could not parse JSON data'})
    
    print("Connecting to database...")
    connection = connect(HOST, PORT, USER, PASSWORD, DATABASE)

    if(not connection):
        return({'error':101, 'message':'Could not connect to database'})
    
    # Expected Params: 
    prompt = data['prompt']

    # Optional Params: 
    #nvector = 10 if 'nvector' not in data else data['nvector']
    model = 'gpt-3.5-turbo-1106' if 'model' not in data else data['model']
    chat_id = new_chat(connection, prompt, 'yggy') if 'chat_id' not in data else data['chat_id']

    chatter = Chatter(model)

    loremaster_dialogue = [] 
    if("chat_id" in data):
        loremaster_dialogue = recreate_loremaster_dialogue(connection, chat_id)

    append_message(connection, chat_id, prompt, 'user')

    reply, _, associated_ids, _ = yggy_step(prompt, chatter, 'text-embedding-3-small', previous_prompts=[], verbose=False, loremaster_dialogue = loremaster_dialogue, connection=connection, host=HOST, port=PORT, user=USER, password=PASSWORD, database=DATABASE)

    append_message(connection, chat_id, reply, 'assistant', associated_ids)

    return({'response':reply}, 200)

@yggy_blueprint.route('/yggy', methods=['GET'])
def yggy_page():
    return render_template('yggy.html')


login_blueprint = Blueprint('login', __name__) 
@login_blueprint.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    connection = connect(HOST, PORT, USER, PASSWORD, DATABASE)
    if(not connection):
        return({'error':101, 'message':'Could not connect to database'})
    
    cursor = connection.cursor()
    cursor.execute("SELECT user_id, username, passhash, salt FROM users WHERE email = %s", (email,))

    if(not cursor):
        return({'error':102, 'message':'Could not execute query'})
    
    result = cursor.fetchone()
    if(not result):
        return({'error':103, 'message':'No user found with that email'})
    
    user_id, username, passhash, salt = result
    cursor.close()
    connection.close()

    if(hash_password(password, salt) == passhash):
        session['logged_in'] = True

        # You can also store additional information in the session
        session['user_id'] = user_id
        session['username'] = username
        return redirect(url_for('dashboard'))

    else:
        #return jsonify({'message': 'Login failed'})
        return(redirect(url_for('login.login'))

# Optionally, you can define a route for serving the login page
@login_blueprint.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')  # Assuming you have a login.html template


app.register_blueprint(yggy_blueprint)
app.register_blueprint(login_blueprint)

@app.route('/dashboard')
def dashboard():
    if 'logged_in' in session and session['logged_in']:
        # User is logged in, allow access to dashboard
        return render_template('dashboard.html')
    else:
        # User is not logged in, redirect to login page
        return redirect(url_for('login.login'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login.login'))

@app.route("/")
def landing_page():
    return render_template('index.html')

app.secret_key = os.urandom(24)

if __name__ == '__main__':
    paresr = make_parser()
    args = parser.parse_args()

    app.run(host='0.0.0.0', port=8098)
