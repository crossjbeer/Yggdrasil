import psycopg2

def connect(host, port, user, password, database, *args, **kwargs):
    # Connect to the PostgreSQL database
    try:
        connection = psycopg2.connect(host=host, port=port, user=user, password=password, database=database )
        return connection
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL:", error)
        return None