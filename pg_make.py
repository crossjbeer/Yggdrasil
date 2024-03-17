import argparse
from pgvector.psycopg2 import register_vector

from pg_utils import connect
from parsers import parser_sql

def make_parser():
    parser = argparse.ArgumentParser()
    
    parser.add_argument('--notes', action='store_true', help='Create note table')
    parser.add_argument('--chats', action='store_true', help='Create chat table')
    parser.add_argument('--chat_text', action='store_true', help='Create chat text table')
    parser.add_argument('--users', action='store_true', help='Create user table')
    parser.add_argument('--planarverses', action='store_true', help='Create planarverse table')
    parser.add_argument('--planes', action='store_true', help='Create plane table')
    parser.add_argument('--sessions', action='store_true', help='Create session table')

    parser = parser_sql(parser)
    return(parser)

def create_note(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE notes (
            id SERIAL PRIMARY KEY,
            content TEXT,
            note VARCHAR(255),
            start_line INT, 
            end_line INT,
            embedding vector(1536),  
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            namespace VARCHAR(255)
        )""")
    conn.commit()
    cursor.close()

def create_chats(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE chats (
                chat_id SERIAL PRIMARY KEY,
                title VARCHAR(255),
                date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                interactions INT,
                process VARCHAR(255)
        )
        """)
    
    conn.commit()
    cursor.close()

def create_chat_text(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE chat_text (
                chat_id INT,
                text_id SERIAL PRIMARY KEY,
                text TEXT,
                role VARCHAR(255),
                chat_ind INT,
                FOREIGN KEY (chat_id) REFERENCES chats(chat_id),
                process VARCHAR(255),
                related_chats INT[],
                date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
    
    conn.commit()
    cursor.close()

def create_users(conn):
    cursor = conn.cursor()
    if(not cursor):
        print("Failed to create cursor")
        return(None)
    
    cursor.execute("""CREATE TABLE users (
user_id SERIAL PRIMARY KEY,
date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
username VARCHAR(255) UNIQUE NOT NULL,
passhash VARCHAR(255) NOT NULL,
salt VARCHAR(255) NOT NULL,
email VARCHAR(255) UNIQUE NOT NULL,
first_name VARCHAR(255),
last_name VARCHAR(255),
bio TEXT,
profile_pic TEXT,
last_login TIMESTAMP,
last_ip VARCHAR(255),
last_session VARCHAR(255),
is_admin BOOLEAN DEFAULT FALSE,
is_active BOOLEAN DEFAULT FALSE,
is_verified BOOLEAN DEFAULT FALSE,
is_staff BOOLEAN DEFAULT FALSE,
is_superuser BOOLEAN DEFAULT FALSE,
is_banned BOOLEAN DEFAULT FALSE)""")
    
    conn.commit()
    cursor.close()
    return()

def create_planarverses(conn):
    cursor = conn.cursor()
    if(not cursor):
        print("Failed to create cursor")
        return(None)
    
    cursor.execute("""CREATE TABLE planarverses (
        verse_id SERIAL PRIMARY KEY,
        date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,   
        user_id INT REFERENCES users(user_id) NOT NULL,
        title VARCHAR(255),
        description TEXT,
        planes_n INT DEFAULT 0
    )""")
    
    conn.commit()
    cursor.close()
    return() 

def create_planes(conn):
    cursor = conn.cursor()
    if(not cursor):
        print("Failed to create cursor")
        return(None)
    
    cursor.execute("""CREATE TABLE planes (
plane_id SERIAL PRIMARY KEY,
verse_id INT REFERENCES planarverses(verse_id),
title VARCHAR(255),
description TEXT)""")
    
    conn.commit()
    cursor.close()
    return()

def create_sessions(conn):
    cursor = conn.cursor()
    if(not cursor):
        print("Failed to create cursor")
        return(None)
    
    cursor.execute("""CREATE TABLE sessions (
session_id SERIAL PRIMARY KEY,
date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
user_id INT REFERENCES users(user_id) NOT NULL,
ip VARCHAR(255),
session VARCHAR(255),
last_login TIMESTAMP,
last_ip VARCHAR(255),
last_session VARCHAR(255));
""")
    
    conn.commit()
    cursor.close()
    return()


def main():
    parser = make_parser()
    args = parser.parse_args()

    conn = connect(**vars(args))
    if(not conn):
        print("Unable to connect to database")
        exit()

    register_vector(conn)

    if(args.notes and args.notes_table):
        print("Building Notes Table")
        create_note(conn)

    if(args.chats and args.chats_table):
        print("Building Chats Table")
        create_chats(conn)

    if(args.chat_text and args.chat_text_table):
        print("Building Chats Text Table")
        create_chat_text(conn)

    if(args.users and args.users_table):
        print("Building Users Table")
        create_users(conn)

    if(args.planarverses and args.planarverses_table):
        print("Building Planarverses Table")
        create_planarverses(conn)

    if(args.planes and args.planes_table):
        print("Building Planes Table")
        create_planes(conn)

    if(args.sessions and args.sessions_table):
        print("Building Sessions Table")
        create_sessions(conn)


    conn.close()

if __name__ == "__main__":
    main() 

