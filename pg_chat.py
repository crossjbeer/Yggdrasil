import psycopg2
from psycopg2 import sql

import openai
import os 

from chatter import Chatter

openai.api_key = os.getenv('OPENAI_AUTH')

def connect(host, port, user, password, database, *args, **kwargs):
    # Connect to the PostgreSQL database
    try:
        connection = psycopg2.connect(host=host, port=port, user=user, password=password, database=database )
        return connection
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL:", error)
        return None

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
            #return [text[0] for text in texts]
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

            return(res[0])
    except psycopg2.Error as e:
        connection.rollback()
        print("Error appending message:", e)



def append_message(connection, chat_id, text, role, table_name='chat_text', chat_id_col='chat_id', text_col='text', role_col='role'):
    # Append a new message to the specified table with the given parameters
    try:
        with connection.cursor() as cursor:
            last_ind = get_last_ind(connection, chat_id)

            # Insert new message
            insert_query = sql.SQL("INSERT INTO {} ({}, {}, {}, chat_ind) VALUES (%s, %s, %s, %s);").format(
                sql.Identifier(table_name),
                sql.Identifier(chat_id_col),
                sql.Identifier(text_col),
                sql.Identifier(role_col)
            )
            cursor.execute(insert_query, (chat_id, text, role, last_ind + 1))

            # Increment interactions in 'chats' table
            update_query = sql.SQL("UPDATE chats SET interactions = interactions + 1 WHERE {} = %s;").format(
                sql.Identifier(chat_id_col)
            )
            cursor.execute(update_query, (chat_id,))

            # Commit the changes
            connection.commit()
            #print("Message appended successfully")
    except psycopg2.Error as e:
        connection.rollback()
        print("Error appending message:", e)

def start_chat(connection, initial_message, role, table_name='chat_text', chat_id_col='chat_id', text_col='text', role_col='role', title=True):
    # Start a new chat with an initial message
    if(title):
        chat = Chatter('gpt-3.5-turbo')
        messages = []

        messages.append(chat.getUsrMsg('Please read the following message. Create a title describing the intention this message. If a suitable title cannot be made, please write <None>. DO NOT preface your title. DO NOT write anything after. DO NOT write things like <summary:> or <title:>'))
        messages.append(chat.getUsrMsg(initial_message))

        reply = chat.passMessagesGetReply(messages)

        title_str = reply

    try:
        with connection.cursor() as cursor:
            # Insert initial message
            cursor.execute("INSERT INTO chats (interactions, title) VALUES (1, %s);", (title_str,))
        
            # Get the newly created chat_id
            cursor.execute("SELECT LASTVAL();")
            chat_id = cursor.fetchone()[0]

            # Create entry in 'chats_text' table
            insert_query = sql.SQL("INSERT INTO {} ({}, {}, {}, chat_ind) VALUES (%s, %s, %s, 1);").format(
                sql.Identifier(table_name),
                sql.Identifier(chat_id_col),
                sql.Identifier(text_col),
                sql.Identifier(role_col),
            )
            cursor.execute(insert_query, (chat_id, initial_message, role))

            # Commit the changes
            connection.commit()
            #print("Chat started successfully. Chat ID:", chat_id)
            return(chat_id)
    except psycopg2.Error as e:
        connection.rollback()
        print("Error starting chat:", e)


def main():
    # Example usage:
    db_params = {
        "user": "crossland",
        "password": "pass",
        "host": "localhost",
        "port": "",
        "database": "yggdrasil"
    }

    connection = connect(db_params)

    if(not connection):
        exit()

    # Example 1: List titles
    titles = list_titles(connection, table_name='chats', title_col='title')
    print("Titles:", titles)

    # Example 2: Grab text from chat with id = 1
    chat_id = 1
    chat_texts = grab_chat(connection, chat_id, table_name='chat_text', chat_id_col='chat_id', text_col='text', text_id_col='text_id')
    print(f"Texts from chat {chat_id}:", chat_texts)

    start_chat(connection, 'how much wood could a wood chuck chuck if a wood chuck chucked wood', 'user')
    append_message(connection, 4, 'Im a cute lil guy', 'assistant')
    get_last_ind(connection, 3)

if(__name__ == "__main__"):
    main()