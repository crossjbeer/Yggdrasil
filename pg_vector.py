import os 
import numpy as np 
import pandas as pd 
from pgvector.psycopg2 import register_vector
from pg_embed import create_embedding

import openai 
openai.api_key = os.getenv('OPENAI_AUTH')

from pg_chat import connect 

def grab_k(search_vector, host, port, user, password, database, notes_table='notes', k=1, namespace=None, *args, **kwargs):
    connection = connect(host, port, user, password, database)
    if(not connection):
        exit("No Connection")

    register_vector(connection)

    cursor = connection.cursor() 
    if(not cursor):
        connection.close()
        exit("No Cursor")

    if(not isinstance(search_vector, np.ndarray)):
        try:
            search_vector = np.asarray(search_vector)
        except Exception as e:
            print("Unable to convert given vector to np array")
            print(e)
            exit()

    if(namespace):
        query = "SELECT content, note, start_line, end_line FROM {} WHERE namespace = %s ORDER BY (embedding <=> %s) LIMIT {};".format(notes_table, k)
    else:
        query = "SELECT content, note, start_line, end_line FROM {} ORDER BY (embedding <=> %s) LIMIT {};".format(notes_table, k)

    try:
        cursor.execute(query, (namespace, search_vector,))
        columns = [desc[0] for desc in cursor.description]

        res = cursor.fetchall()
        res_dict = {col:[] for col in columns}

        for r in res: 
            for col, rval in zip(columns, r): 
                res_dict[col].append(rval)

        return(res_dict)
    
    except Exception as e: 
        print("Error in grab_k")
        exit(e)



def test(search_vector, host, port, user, password, database, notes_table='notes', limit=1):
    connection = connect(host, port, user, password, database)
    if(not connection):
        exit("No Connection")

    register_vector(connection)

    cursor = connection.cursor() 
    if(not cursor):
        connection.close()
        exit("No Cursor")

    if(not isinstance(search_vector, np.ndarray)):
        try:
            search_vector = np.asarray(search_vector)
        except Exception as e:
            print("Unable to convert given vector to np array")
            print(e)
            exit()

    query = "SELECT content, note, start_line, end_line FROM {} ORDER BY (embedding <=> %s) LIMIT {};".format(notes_table, limit)

    try:
        cursor.execute(query, (search_vector,))
        columns = [desc[0] for desc in cursor.description]
        print(columns)
        res = cursor.fetchall()
        print(res)
        res = {columns[i]:res[i] for i in range(len(columns))}

        return(res)
    
    except Exception as e:
        print("Yes")
        print(e)
        print("No")


def main():
    embed_response = create_embedding('who is har barkem?')
    embedding = embed_response['data'][0]['embedding']

    test(embedding, 'localhost', '', 'crossland', 'pass', 'yggdrasil')


if(__name__ == "__main__"):
    main()
