from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import json 
import argparse 

# Google Docs API scopes
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']

def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--force', help='Force overwrite of existing files.', action='store_true')
    return(parser)


def authenticate():
    creds = None

    # The file token.json stores the user's access and refresh tokens
    token_path = 'token.json'

    # Check if token file exists and is valid
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path)

    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return creds

def download_doc(service, doc_id, output_file):
    doc = service.documents().get(documentId=doc_id).execute()
    content = doc['body']['content']

    # Extract text content from the document
    text_content = ""
    for paragraph in content:
        if 'paragraph' in paragraph:
            elements = paragraph['paragraph']['elements']
            for element in elements:
                if 'textRun' in element:
                    text_content += element['textRun']['content']

    # Save content to a text file
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(text_content)


def main():
    parser = make_parser() 
    args = parser.parse_args()

    creds = authenticate()
    service = build('docs', 'v1', credentials=creds)

    docs_ids = json.load(open("./notes.json",'r'))

    for doc_name, doc_id in docs_ids.items():
        output_file = f'./notes/{doc_name}'

        if(os.path.exists(output_file) and not args.force):
            print(f'File {output_file} already exists, skipping.')
            continue

        download_doc(service, doc_id, output_file)
        print(f'Successfully downloaded {doc_name} to {output_file}')

if __name__ == '__main__':
    main()



