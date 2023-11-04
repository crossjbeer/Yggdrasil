import mysql.connector
import argparse

# Connect to the MySQL database
def connect_to_database(host, user, password, database):
    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )
    return connection

# Retrieve data from the 'text' column and prompt the user for input
def retrieve_data_and_prompt(host, user, password, database, table, session, session_name, whisper, startingline=0):
    connection = connect_to_database(host, user, password, database)
    cursor = connection.cursor()

    query = f"SELECT class, text, session_id FROM {table} WHERE session = %s AND session_name = %s AND whisper = %s;"
    cursor.execute(query, (session, session_name, whisper))
    rows = cursor.fetchall()

    dnd_class = []  # List to store the user input

    #all_rows = len(rows)

    for i, row in enumerate(rows[startingline:]):
        c, text, session_id = row[0], row[1], row[2]
        print("{}: <{}> ".format(startingline+i, c), text)
        response = input("Enter 0/1: ")

        if(not len(response)):
            response = '0'

        dnd_class.append(int(response))

        # Update the MySQL table with the user response
        update_query = f"UPDATE {table} SET dnd_class = %s WHERE session_id = %s AND session = %s AND session_name = %s AND whisper = %s;"
        cursor.execute(update_query, (int(response), session_id, session, session_name, whisper))
        connection.commit()

    cursor.close()
    connection.close()

    return dnd_class

# Main function to run the script
if __name__ == '__main__':
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='MySQL Data Scraper')
    parser.add_argument('-H', '--host', type=str, default='localhost', help='MySQL host')
    parser.add_argument('-u', '--user', type=str, required=False, default='ygg', help='MySQL username')
    parser.add_argument('-p', '--password', type=str, default='', help='MySQL password')
    parser.add_argument('-d', '--database', type=str, required=False, default='yggdrasil', help='MySQL database')
    parser.add_argument('-t', '--table', type=str, required=False, default='transcript', help='MySQL table')
    parser.add_argument('-s', '--session', type=str, help='Session criteria')
    parser.add_argument('-sn', '--session-name', type=str, help='Session name criteria')
    parser.add_argument('-w', '--whisper', type=str, help='Whisper criteria')
    parser.add_argument("-sl", '--startingline' , type=int, help='Line of the transcript to start classifying', default=0)
    
    args = parser.parse_args()

    dnd_class = retrieve_data_and_prompt(
        args.host, args.user, args.password, args.database, args.table,
        args.session, args.session_name, args.whisper, args.startingline
    )
    print("dnd_class:", dnd_class)