import psycopg2
from psycopg2 import sql
import openai
import os 
from pg_utils import connect 

from chatter import Chatter

openai.api_key = os.getenv('OPENAI_AUTH')

def list_titles(connection, table_name='chats', title_col='title'):
    # List titles from the specified table
    try:
        with connection.cursor() as cursor:
            query = sql.SQL("SELECT {} FROM {};").format(
                sql.Identifier(title_col),
                sql.Identifier(table_name)
            )
            cursor.execute(query)
            titles = cursor.fetchall()
            return [title[0] for title in titles]
    except psycopg2.Error as e:
        print("Error fetching titles:", e)
        return None
    
def ids_and_titles(connection, chat_table='chats', id_col='chat_id', title_col='title', *args, **kwargs):
    try:
        with connection.cursor() as cursor:
            query = sql.SQL("SELECT {}, {} FROM {};").format(
                sql.Identifier(id_col),
                sql.Identifier(title_col),
                sql.Identifier(chat_table)
            )
            cursor.execute(query)
            tuples = cursor.fetchall()
            return [t for t in tuples]
    except psycopg2.Error as e:
        print("Error fetching titles:", e)
        return None
    
def grab_chat(connection, chat_id, chat_text_table='chat_text', chat_id_col='chat_id', text_col='text', role_col='role', text_id_col='text_id', *args, **kwargs):
    # Get text from the specified table with the given parameters
    try:
        with connection.cursor() as cursor:
            query = sql.SQL("SELECT {}, {} FROM {} WHERE {} = %s ORDER BY {};").format(
                sql.Identifier(role_col),
                sql.Identifier(text_col),
                sql.Identifier(chat_text_table),
                sql.Identifier(chat_id_col),
                sql.Identifier(text_id_col)
            )
            cursor.execute(query, (chat_id,))
            texts = cursor.fetchall()
            return(texts)
    except psycopg2.Error as e:
        print("Error grabbing chat:", e)
        return None

def get_last_ind(connection, chat_id):
    try:
        with connection.cursor() as cursor:
            query = "SELECT MAX(chat_ind) FROM chat_text WHERE chat_id = %s;"

            cursor.execute(query, (chat_id,))
            res = cursor.fetchone()

            if(len(res) == 0 or res[0] == None):
                return(0)

            return(res[0])
    except psycopg2.Error as e:
        connection.rollback()
        print("Error appending message:", e)

def append_message(connection, chat_id, text, role, associated_ids = [], table_name='chat_text', chat_id_col='chat_id', text_col='text', role_col='role', chat_ind_col='chat_ind', ass_ids_col='related_chats'):
    # Append a new message to the specified table with the given parameters
    try:
        with connection.cursor() as cursor:
            last_ind = get_last_ind(connection, chat_id)

            #insert_query = f"INSERT INTO {table_name} ({chat_id_col}, {text_col}, {role_col}, {chat_ind_col}, {ass_ids_col}) VALUES (%s, %s, %s, %s, %s);"
            if(not len(associated_ids)):
                insert_query = f"INSERT INTO {table_name} ({chat_id_col}, {text_col}, {role_col}, {chat_ind_col}) VALUES (%s, %s, %s, %s);"
                values = (chat_id, text, role, last_ind + 1,)
            else:
                insert_query = f"INSERT INTO {table_name} ({chat_id_col}, {text_col}, {role_col}, {chat_ind_col}, {ass_ids_col}) VALUES (%s, %s, %s, %s, %s);"
                values = (chat_id, text, role, last_ind+1, associated_ids)

            cursor.execute(insert_query, values)

            # Increment interactions in 'chats' table
            update_query = sql.SQL("UPDATE chats SET interactions = interactions + 1 WHERE {} = %s;").format(
                sql.Identifier(chat_id_col)
            )
            cursor.execute(update_query, (chat_id,))

            # Commit the changes
            connection.commit()
    except psycopg2.Error as e:
        connection.rollback()
        print("Error appending message:", e)

def title_chat(initial_message, chat, title_msg=None):
    messages = []
    messages.append(chat.getUsrMsg('Please read the following message. Create a title describing the intention this message. If a suitable title cannot be made, please write <None>. DO NOT preface your title. DO NOT write anything after. DO NOT write things like <summary:> or <title:>'))

    if(title_msg):
        messages.append(chat.getUsrMsg(title_msg))
    else:
        messages.append(chat.getUsrMsg(initial_message))

    reply = chat.passMessagesGetReply(messages)

    title_str = reply
    if(title_str == '<None>' or title_str == 'None' or title_str == 'none' or title_str == 'NONE' or title_str == '' or len(title_str) > 255):
        title_str = initial_message

    return(title_str)

def new_chat(connection, initial_user_query, process, chats_table='chats', title_model='gpt-3.5-turbo-1106'):
    chat = Chatter(title_model)
    title = title_chat(initial_user_query, chat)

    try:
        with connection.cursor() as cursor:
            cursor.execute(f"INSERT INTO {chats_table} (interactions, title, process) VALUES (0, %s, %s);", (title, process,))
            cursor.execute("SELECT LASTVAL();")
            chat_id = cursor.fetchone()[0]
            return chat_id
        
    except Exception as e: 
        connection.rollback()
        print("Error starting chat:", e)
        return None
    
def recreate_loremaster_dialogue(connection, yggy_chat_id, chats_table='chats', chat_text_table = 'chat_text'):
    # We want to get the chats related to each assistant response in the yggy chat
    msg_query = f"SELECT related_chats FROM {chat_text_table} WHERE chat_id = %s ORDER BY text_id;"

    try:
        with connection.cursor() as cursor:
            cursor.execute(msg_query, (yggy_chat_id,))
            related_chats_per_msg = cursor.fetchall()
    except Exception as e:
        print("Error fetching related chats:", e)
        return None
    
    # Now we have a list of lists, where each list is a chat_id of a chat related to the yggy assistant response
    loremaster_chat_ids = [] 
    for related_chats in related_chats_per_msg:
        related_chats = related_chats[0]
        if(related_chats is None or not len(related_chats)):
            continue 
        try:
            with connection.cursor() as cursor:
                for related_chat in related_chats: 
                    print(related_chat)
                    cursor.execute(f"SELECT process FROM {chats_table} WHERE chat_id = %s;", (related_chat,))
                    process = cursor.fetchall()

                    if(len(process)):
                        process = process[0][0]

                    if(process == 'loremaster'):
                        loremaster_chat_ids.append(related_chat)
                        break 

        except Exception as e:
            print("Error fetching chat processes:", e)
            return None
        
    # We have a list of loremaster chats that went to building the yggy chat. Now let's pull all the loremaster assistant responses from each of these... 
    loremaster_responses = []
    for chat_id in loremaster_chat_ids:
        chat_responses = grab_chat(connection, chat_id)

        if(not len(loremaster_responses)):
            # Grab the system prompt 
            loremaster_responses.append(chat_responses[0])

        for i in range(-1, -len(chat_responses)-1, -1):

            if(chat_responses[i][0] == 'assistant'):
                # Grab the full igor response and the loremaster response
                loremaster_responses.append(chat_responses[i-1])
                loremaster_responses.append(chat_responses[i])
                break

    return(loremaster_responses)



def main():
    # Example usage:
    db_params = {
        "user": "crossland",
        "password": "pass",
        "host": "localhost",
        "port": "",
        "database": "yggdrasil"
    }

    connection = connect(**db_params)

    if(not connection):
        exit()
    """
    # Example 1: List titles
    titles = list_titles(connection, table_name='chats', title_col='title')
    print("Titles:", titles)

    # Example 2: Grab text from chat with id = 1
    chat_id = 1
    chat_texts = grab_chat(connection, chat_id, table_name='chat_text', chat_id_col='chat_id', text_col='text', text_id_col='text_id')
    print(f"Texts from chat {chat_id}:", chat_texts)

    start_chat(connection, 'how much wood could a wood chuck chuck if a wood chuck chucked wood', 'user')
    append_message(connection, 4, 'Im a cute lil guy', 'assistant')
    get_last_ind(connection, 3)"""

    #print(recreate_loremaster_dialogue(connection, 67))
    dlog = recreate_loremaster_dialogue(connection, 67)
    for msg in dlog:
        print(msg)
        print()

if(__name__ == "__main__"):
    main()