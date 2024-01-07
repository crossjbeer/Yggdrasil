from argparse import ArgumentParser

def combine_parsers(parser1, parser2, combined_description='Combined Parser'):
    combined_parser = ArgumentParser(description=combined_description)

    # Add arguments from parser1 to combined_parser
    for action in parser1._actions:
        if('-h' in action.option_strings):
            continue 
        combined_parser._add_action(action)

    # Add arguments from parser2 to combined_parser
    for action in parser2._actions:
        # Check if an argument with the same option strings already exists in the combined_parser
        if not any(action.option_strings == existing_action.option_strings for existing_action in combined_parser._actions):
            combined_parser._add_action(action)

    return combined_parser

def make_parser_sql():
    parser = ArgumentParser(description = "Providing Default Postgres Arguments!")

    parser.add_argument('-H', '--host', help='Postgres Host (Default: localhost)', type=str, default='localhost')
    parser.add_argument('-po', '--port', help='Postgres Port (Default: "")', type=str, default='')
    parser.add_argument('-u', '--user', help='Postgres User (Default: crossland)', type=str, default='crossland')
    parser.add_argument('-db', '--database', help='Postgres Database (Default: yggdrasil)', type=str, default='yggdrasil')
    parser.add_argument('-pw', '--password', help='Postgres Password (Default: pass)', type=str, default='pass')

    parser.add_argument('--transcript_table', help='Postgres transcript table (Default: transcript)', default='transcript', type=str)
    parser.add_argument('--note_table', help='Postgres note table (Default: notes)', default='notes', type=str)

    return(parser)

def make_parser_gpt():
    parser = ArgumentParser(description='Providing GPT Arguments!')

    parser.add_argument('-q', '--query', help='Query for Chat GPT', type=str, default=None, required=False)
    parser.add_argument('-m', '--model', help='Open AI model to use [gpt3.5-turbo, gpt4] (Default: gpt-3.5-turbo)', type=str, default='gpt-3.5-turbo')
    parser.add_argument('-n', '--nvector', help='Number of vectors to query', type=int, default=3)
    parser.add_argument('-eb', '--embedder', help='Open AI Embedding Model (Default: text-embedding-ada-002)', default='text-embedding-ada-002', type=str)

    return(parser)


def make_parser_gpt_sql():
    gpt_parser = make_parser_gpt()
    sql_parser = make_parser_sql()

    parser = combine_parsers(gpt_parser, sql_parser, "Grab args for GPT + SQL")
    return(parser)


def main():
    parser = make_parser_gpt_sql()

    parser.parse_args()

if(__name__ == "__main__"):
    main()