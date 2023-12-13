import psycopg2
import argparse 

from chatter import Chatter 
from colorcodes import Colorcodes

from postgre_chat import start_chat, append_message, connect, ids_and_titles, grab_chat

def make_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('--host', help='MySQL host', required=False, default='localhost')
    parser.add_argument("--port", help='Postgres Port', default="")
    parser.add_argument('-d', '--database', help='MySQL database', required=False, default='yggdrasil')
    parser.add_argument('-u', '--user', help='Postgre User', default='crossland')
    parser.add_argument('-pw', '--password', help='Postgre Pass', default='pass')
    parser.add_argument('--chat_table', help='Table containing info on chats.',default='chats')
    parser.add_argument('--chat__text_table', help='Table containing chat text', default='chats')
    parser.add_argument('-m', "--model", help='GPT Model (gpt-3.5-turbo)', default='gpt-3.5-turbo', type=str)

    return(parser)

def get_title_ind(avail_id):
    title_ind = None 
    while title_ind is None:
        inp = input('> ')

        try:
            inp = int(inp)
        except:
            print("Invalid Entry")
            continue

        if(inp not in avail_id):
            print("Invalid Entry")
            continue 

        title_ind = inp

    return(title_ind)


def main():
    parser = make_parser()
    args = parser.parse_args()

    connection = connect(**vars(args))

    chat = Chatter(args.model)
    color = Colorcodes()

    id_and_tit = ids_and_titles(connection, **vars(args))

    print(color.pbold("Titles:"))
    for id, title in sorted(id_and_tit, key=lambda x: x[0]):
        print(color.pbold("{}: {}".format(id, title)))

    chat_id = get_title_ind([idt[0] for idt in id_and_tit])

    messages = grab_chat(connection, chat_id=chat_id, **vars(args))
    messages = [{'role':msg[0], 'content':msg[1]} for msg in messages]

    chat.printMessages(messages)

    


    

if(__name__ == "__main__"):
    main()