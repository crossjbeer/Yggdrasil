import argparse
import psycopg2
from pgvector.psycopg2 import register_vector

def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", help="Database host (Default: localhost)", default="localhost", type=str)
    parser.add_argument("--port", help="Database port (Default: '')", default="", type=str)
    parser.add_argument("--database", help="Database name (Default: yggy)", default="yggy", type=str)
    parser.add_argument("--user", help="Database user (Default: crossland)", default="crossland", type=str)
    parser.add_argument("--password", help="Database password (Default: pass)", default="pass", type=str)

    return(parser)

def create_table(conn):
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

def main():
    parser = make_parser()
    args = parser.parse_args()

    conn = psycopg2.connect(**vars(args))
    if(not conn):
        print("Unable to connect to database")
        exit()

    register_vector(conn)

    create_table(conn)
    conn.close()

if __name__ == "__main__":
    main() 
