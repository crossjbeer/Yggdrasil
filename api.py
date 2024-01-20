from flask import Flask, Blueprint, request
from openai import OpenAI 
import os
import argparse

#from parsers import make_parser_gpt_sql
from parsers import parser_gpt, parser_sql

from pg_chat import connect, grab_chat, start_chat, append_message
from noting import ask_igor, ask_loremaster, orchestrate_step

from chatter import Chatter 

HOST = 'localhost'
PORT = '5432'
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
@noting_blueprint.route('/yggy', methods=['GET'])
def yggy():
    prompt = request.args.get('prompt')
    user = request.args.get('user')
    password = request.args.get('password')
    #campaign = request.args.get('campaign')

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

    chatter = Chatter(model)
    reply = orchestrate_step(prompt, model, chatter, nvector, embedder, verbose=False, loremaster_dialogue=messages, host=HOST, port=PORT, user=user, password=password, database=DATABASE)



    #append_message(connection, chat_id, messages[-1]['content'], role='user')
    #append_message(connection, chat_id, loremaster_reply, role='assistant')
    return({'response':reply}, 200)
    


app.register_blueprint(chat_blueprint)
app.register_blueprint(noting_blueprint)
if __name__ == '__main__':
    parser = make_parser_gpt_sql()
    args = parser.parse_args()

    app.run(host='0.0.0.0')
