import argparse
from pg_chat import connect
from pgvector.psycopg2 import register_vector

def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", help="Database host (Default: localhost)", default="localhost", type=str)
    parser.add_argument("--port", help="Database port (Default: '')", default="", type=str)
    parser.add_argument("--database", help="Database name (Default: yggy)", default="yggy", type=str)
    parser.add_argument("--user", help="Database user (Default: crossland)", default="crossland", type=str)
    parser.add_argument("--password", help="Database password (Default: pass)", default="pass", type=str)

    parser.add_argument('--no_note', action='store_true', help='Do not create note table')
    parser.add_argument('--no_chat', action='store_true', help='Do not create chat table')
    parser.add_argument('--no_chat_text', action='store_true', help='Do not create chat text table')
    return(parser)

def create_note_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE notes (
            id SERIAL PRIMARY KEY,
            content TEXT,
            note VARCHAR(255),
            start_line INT, 
            end_line INT,
            embedding vector(1536),  
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    conn.commit()
    cursor.close()

def create_chats_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE chats (
                chat_id SERIAL PRIMARY KEY,
                title VARCHAR(255),
                date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                interactions INT
        )
        """)
    
    conn.commit()
    cursor.close()

def create_chat_text_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE chat_text (
                chat_id INT,
                text_id SERIAL PRIMARY KEY,
                text VARCHAR(255),
                role VARCHAR(255),
                chat_ind INT,
                FOREIGN KEY (chat_id) REFERENCES chats(chat_id)
        )
        """)
    
    conn.commit()
    cursor.close()

def main():
    parser = make_parser()
    args = parser.parse_args()

    #conn = psycopg2.connect(**vars(args))
    conn = connect(**vars(args))
    if(not conn):
        print("Unable to connect to database")
        exit()

    register_vector(conn)

    if(not args.no_note):
        print("Building Notes Table")
        create_note_table(conn)

    if(not args.no_chat):
        print("Building Chats Table")
        create_chat_table(conn)

    if(not args.no_chat_text):
        print("Building Chats Text Table")
        create_chat_text_table(conn)

    conn.close()

if __name__ == "__main__":
    main() 
