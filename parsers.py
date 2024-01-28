def valid_path(path):
    import os 
    if(not os.path.exists(path)):
        raise ValueError(f'Path {path} does not exist')
    return(path)

def valid_path_build(path):
    import os 
    if(not os.path.exists(path)):
        os.makedirs(path)
    return(path)

def parser_sql(parser):
    parser.add_argument('-H', '--host', help='Postgres Host (Default: localhost)', type=str, default='localhost')
    parser.add_argument('-po', '--port', help='Postgres Port (Default: "")', type=str, default='')
    parser.add_argument('-u', '--user', help='Postgres User (Default: crossland)', type=str, default='crossland')
    parser.add_argument('-pw', '--password', help='Postgres Password (Default: pass)', type=str, default='pass')
    parser.add_argument('-db', '--database', help='Postgres Database (Default: yggdrasil)', type=str, default='yggdrasil')
    
    parser.add_argument('--transcript_table', help='Postgres transcript table (Default: transcript)', default='transcript', type=str)
    parser.add_argument('--notes_table', help='Postgres note table (Default: notes)', default='notes', type=str)
    parser.add_argument('--chats_table', help='Postgres chat table (Default: chats)', default='chats', type=str)
    parser.add_argument('--chat_text_table', help='Postgres chat text table (Default: chat_text)', default='chat_text', type=str)
    parser.add_argument('--users_table', help='Postgres users table (Default: users)', default='users', type=str)
    parser.add_argument('--planarverses_table', help='Postgres planarverses table (Default: planarverses)', default='planarverses', type=str)
    parser.add_argument('--planes_table', help='Postgres planes table (Default: planes)', default='planes', type=str)
    parser.add_argument('--sessions_table', help='Postgres sessions table (Default: sessions)', default='sessions', type=str)

    return(parser)

def parser_gpt(parser):
    parser.add_argument('-q', '--query', help='Query for Chat GPT', type=str, default=None, required=False)
    parser.add_argument('-m', '--model', help='Open AI model to use [gpt3.5-turbo, gpt4] (Default: gpt-3.5-turbo-1106)', type=str, default='gpt-3.5-turbo-1106')
    parser.add_argument('-n', '--nvector', help='Number of vectors to query', type=int, default=5)
    parser.add_argument('-eb', '--embedder', help='Open AI Embedding Model (Default: text-embedding-ada-002)', default='text-embedding-ada-002', type=str)

    return(parser)

def parser_doc(parser):
    parser.add_argument('-p', '--path', help='Path to a .txt file to categorize.', type=valid_path)
    parser.add_argument('--token_lim', help='Number of tokens to chunk the .txt file into.', type=int, default=750)
    parser.add_argument('--lag', type=int, help='Number of tokens to lag between chunks. (Default: 0)', default=0)

    parser.add_argument('--doc_name', help='Name of the document to be parsed.', default=None, type=str)
    parser.add_argument('--doc_desc', help='Description of the document to be parsed.', default=None, type=str)

    return(parser)