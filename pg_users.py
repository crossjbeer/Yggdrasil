import secrets
import hashlib
import argparse 

from parsers import parser_sql
from pg_utils import connect 

def make_parser():
    parser = argparse.ArgumentParser() 

    parser.add_argument('-un', '--username', type=str, help='Username', required=True)
    parser.add_argument('-upw', '--user_password', type=str, help='Password', required=True)
    parser.add_argument('-e', '--email', type=str, help='Email')
    parser.add_argument('-fn', '--first_name', type=str, help='First name')
    parser.add_argument('-ln', '--last_name', type=str, help='Last name')
    parser.add_argument('--is_admin', action='store_true', help='Is admin')
    parser.add_argument('--is_active', action='store_true',  help='Is active')
    parser.add_argument('--is_verified', action='store_true',  help='Is verified')
    parser.add_argument('--is_staff', action='store_true',  help='Is staff')
    parser.add_argument('--is_superuser', action='store_true',  help='Is superuser')
    parser.add_argument('--is_banned', action='store_true',  help='Is banned')

    parser = parser_sql(parser)

    return(parser) 

def hash_password(password, salt):
    salted_password = salt + password
    passhash = hashlib.sha256(salted_password.encode()).hexdigest()
    return(passhash)

def new_user(connection, username, password, email, user_metadata, users_table='users', *args, **kwargs):
    cursor = connection.cursor()
    if(not cursor):
        print("Failed to create cursor")
        return(None)
    
    salt = secrets.token_hex(16)  # Generate a random 16-byte salt
    
    # Join salt to password and hash the combination
    passhash = hash_password(password, salt)

    if('is_admin' not in user_metadata):
        user_metadata['is_admin'] = False

    if('is_active' not in user_metadata):
        user_metadata['is_active'] = False 

    if('is_verified' not in user_metadata):
        user_metadata['is_verified'] = False

    if('is_staff' not in user_metadata):
        user_metadata['is_staff'] = False

    if('is_superuser' not in user_metadata):
        user_metadata['is_superuser'] = False

    if('is_banned' not in user_metadata):
        user_metadata['is_banned'] = False

    query = f"""INSERT INTO {users_table} (username, passhash, salt, email, """
    values = [username, passhash, salt, email]

    for key, value in user_metadata.items():
        query += f"{key}, "
        values.append(value)

    query = query.rstrip(", ")  # Remove the trailing comma
    query += ") VALUES ("

    for _ in range(len(values)):
        query += "%s, "

    query = query.rstrip(", ")  # Remove the trailing comma
    query += ") RETURNING user_id;"

    # Execute the query using the values
    cursor.execute(query, values)
    connection.commit()

    # Get the user_id from the result
    user_id = cursor.fetchone()[0]

    return user_id

def main():
    parser = make_parser()
    args = parser.parse_args()

    connection = connect(**vars(args))

    if(not connection):
        exit()

    user_metadata = {
        'first_name': args.first_name,
        'last_name': args.last_name,

        'is_admin': args.is_admin,
        'is_active': args.is_active,
        'is_verified': args.is_verified,
        'is_staff': args.is_staff,
        'is_superuser': args.is_superuser,
        'is_banned': args.is_banned
    }

    user_id = new_user(connection, args.username, args.user_password, args.email, user_metadata)
    print("New User Created with id:", user_id)

if(__name__ == '__main__'):
    main()