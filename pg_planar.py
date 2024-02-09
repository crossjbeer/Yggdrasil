import argparse 

from parsers import parser_sql
from pg_utils import connect

def make_parser():
    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-uid', '--user_id', help='User ID', type=int)
    group.add_argument('-vid', '--verse_id', help='Verse ID', type=int)

    parser.add_argument('-t', '--title', help='Title', type=str, required=True)
    parser.add_argument('-d', '--description', help='Description', type=str, required=True)

    parser = parser_sql(parser)
    return parser

def new_planarverse(connection, user_id, title, description, planarverses_table='planarverses', *args, **kwargs):
    cursor = connection.cursor()
    if(not cursor):
        print("Failed to create cursor")
        return(None)

    query = f"""INSERT INTO {planarverses_table} (user_id, title, description) VALUES (%s, %s, %s)"""
    values = [user_id, title, description]

    try:
        cursor.execute(query, values)
        connection.commit()
        cursor.close()
        return(True)
    except Exception as e:
        print("Error inserting new planarverse:", e)
        return(False)
    
def new_plane(connection, verse_id, title, description, planes_table='planes', *args, **kwargs):
    cursor = connection.cursor()
    if(not cursor):
        print("Failed to create cursor")
        return(None)

    query = f"""INSERT INTO {planes_table} (verse_id, title, description) VALUES (%s, %s, %s)"""
    values = [verse_id, title, description]

    try:
        cursor.execute(query, values)
        connection.commit()
        cursor.close()
        return(True)
    except Exception as e:
        print("Error inserting new plane:", e)
        return(False)

def main():
    parser = make_parser()
    args = parser.parse_args()

    connection = connect(**vars(args))
    if(not connection):
        exit()

    print("Building new Plane...")
    if(args.user_id):
        new_planarverse(connection, args.user_id, args.title, args.description)
    else:
        new_plane(connection, args.verse_id, args.title, args.description)

if(__name__ == '__main__'):
    main()