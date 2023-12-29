from flask import Flask, Blueprint, request
from openai import OpenAI 
import os 
from parsers import make_parser_gpt_sql
from pg_chat import connect, grab_chat, start_chat, append_message
from noting import ask_igor, ask_loremaster

from chatter import Chatter 

HOST = 'localhost'
PORT = '5432'
DATABASE = 'yggy'

parser = make_parser_gpt_sql()
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

    nvector = 10
    try:
        nvector = request.args.get('nvector')
    except:
        pass

    embedder = 'text-embedding-ada-002'
    try:
        embedder = request.args.get('embedder')
    except:
        pass

    model = 'gpt-3.5-turbo-1106'
    try:
        model = request.args.get('model')
    except:
        pass 

    chat_id = None 
    messages = [] 
    try:
        chat_id = request.args.get('chat_id')
    except:
        pass 

    if(chat_id):
        try:
            messages = grab_chat(connection, chat_id)
        except Exception as e: 
            return({'error':101, 'message':str(e)})
    else:
        chat_id = start_chat(connection, prompt, role='user')

    print("Building Chatter...")
    chatter = Chatter(model)
    try:
        print("Asking IGOR...")
        igor_reply = ask_igor(prompt, embedder, model, nvector, chatter=chatter, verbose=True)

        print("Asking LORE MASTER...")
        loremaster_reply = ask_loremaster(prompt, igor_reply, chatter, messages=messages)

        append_message(connection, chat_id, loremaster_reply, role='assistant')
        return({'response':loremaster_reply})
    
    except Exception as e:  
        return({'error':101, 'message':str(e)})
    


app.register_blueprint(chat_blueprint)
app.register_blueprint(noting_blueprint)
if __name__ == '__main__':
    parser = make_parser_gpt_sql()
    args = parser.parse_args()

    app.run()
