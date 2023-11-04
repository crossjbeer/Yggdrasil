"""
Chat GPT Prompt: 

Let's build our own mysql scraper in python which will use mysql.connector as a backend. 

Attributes: 
1) host
2) db
3) table
4) user
5) pass

Methods:
1) print
-- allow user to print given the names of the columns of the given table
ChatGPT

"""

import mysql.connector
import argparse 

class crawlingClaw:
    def __init__(self, host, db, table, user, password):
        self.host = host
        self.db = db
        self.table = table
        self.user = user
        self.password = password
        self.connection = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                database=self.db,
                user=self.user,
                password=self.password
            )
            print("Connected to MySQL database")
        except mysql.connector.Error as error:
            print("Error connecting to MySQL database:", error)

    def disconnect(self):
        if self.connection:
            self.connection.close()
            print("Disconnected from MySQL database")

    def print_column_vals(self, column_names):
        if not self.connection:
            print("Not connected to a MySQL database. Please call 'connect()' first.")
            return

        cursor = self.connection.cursor()
        columns = ', '.join(column_names)
        query = f"SELECT {columns} FROM {self.table}"

        try:
            cursor.execute(query)
            rows = cursor.fetchall()

            if rows:
                print(', '.join(column_names))
                for row in rows:
                    print(', '.join(str(value) for value in row))
            else:
                print("No data found in the table.")
        except mysql.connector.Error as error:
            print("Error executing query:", error)

        cursor.close()

    def print_column_names(self):
        if not self.connection:
            print("Not connected to a MySQL database. Please call 'connect()' first.")
            return

        try:
            cursor = self.connection.cursor()
            cursor.execute(f"DESCRIBE {self.table}")
            columns = [column[0] for column in cursor.fetchall()]

            print("Columns:")
            print(', '.join(columns))

            cursor.close()
        except mysql.connector.Error as error:
            print("Error executing query:", error)

    
    def print_unique_values(self, column):
        if not self.connection:
            print("Not connected to a MySQL database. Please call 'connect()' first.")
            return

        try:
            cursor = self.connection.cursor()
            query = f"SELECT DISTINCT {column} FROM {self.table}"
            cursor.execute(query)
            values = [str(value) for value in cursor.fetchall()]

            print(f"Unique values in column '{column}':")
            print(', '.join(values))

            cursor.close()
        except mysql.connector.Error as error:
            print("Error executing query:", error)

    def printNull(self, column):
        if not self.connection:
            print("Not connected to a MySQL database. Please call 'connect()' first.")
            return

        try:
            cursor = self.connection.cursor()
            query = f"SELECT {column} FROM {self.table} WHERE {column} IS NULL"
            cursor.execute(query)
            rows = cursor.fetchall()

            if rows:
                print(f"Null values in column '{column}'")
                #for row in rows:
                #    print(', '.join(str(value) for value in row))
            else:
                print(f"No null values found in column '{column}'.")
            
            cursor.close()
        except mysql.connector.Error as error:
            print("Error executing query:", error)

def main():
    parser = argparse.ArgumentParser(description="MySQL Scraper")
    parser.add_argument('--host', help="MySQL host")
    parser.add_argument('--db', help="MySQL database", default='yggdrasil')
    parser.add_argument('--table', help="MySQL table", default='transcript')
    parser.add_argument('--user', help="MySQL user", default='ygg')
    parser.add_argument('--password', help="MySQL password")
    parser.add_argument('--columns', nargs='+', help="Column names", required=False)
    parser.add_argument('--colnames', help='print the column names of self.table', action='store_true')
    parser.add_argument('--unique_vals', nargs='+', help="List of column names to print unique values", required=False)
    parser.add_argument('--null_vals', nargs='+', help="List of column names to print null values", required=False)

    args = parser.parse_args()

    scraper = crawlingClaw(
        host=args.host,
        db=args.db,
        table=args.table,
        user=args.user,
        password=args.password
    )

    scraper.connect()

    if(args.colnames):
        scraper.print_column_names()

    if(args.columns):
        scraper.print_column_vals(args.columns)

    if(args.unique_vals):
        for col in args.unique_vals:
            scraper.print_unique_values(col)

    if args.null_vals:
        for col in args.null_vals:
            scraper.printNull(col)

    scraper.disconnect()

if __name__ == '__main__':
    main()