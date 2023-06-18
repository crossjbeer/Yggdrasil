import openai
import os 
import argparse 
import pinecone 
import pandas as pd 

openai.api_key = os.getenv('OPENAI_AUTH')
# Alternatively just set your own api key (just don't upload to git!)
pinecone.init(api_key = '27f2b80f-96a2-4c4f-baba-262615e29ac2', environment='asia-southeast1-gcp-free')

INDEX = pinecone.Index('ygg')

def embeddingToText(path):
    res = pd.read_csv(path, header=0)

    return({res['index'].values[i] : res['text'].values[i] for i in range(len(res))})

def estimateTokens(s, charPerToken = 4):
    return(len(s) / charPerToken)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-q', '--query', help='Query for Chat GPT', type=str, default=None)
    parser.add_argument('-m', '--model', help='Open AI model to use [gpt3.5-turbo, gpt4]', type=str, default='gpt-4')
    parser.add_argument('-n', '--nvector', help='Number of vectors to query', type=int, default=25)
    parser.add_argument('-p', '--path', type=str, help='Path to directory containing <date> folders with embedding files...')

    args = parser.parse_args() 

    print("Converting query into Embedding...")
    response = openai.Embedding.create(
            input=args.query,
            model='text-embedding-ada-002'
    )
    print("Embedding Complete\n")
    
    embeddings = response['data'][0]['embedding']

    print("Using Embedding to Query Pinecone for top {} Vectors...".format(args.nvector))
    relatedVectors = INDEX.query(
        top_k=args.nvector,
        vector=embeddings ,
        include_values=True
    )
    print("Pinecone Query Complete\n")

    relatedID = [i['id'] for i in relatedVectors['matches']]

    sessionToID = {}
    for id in relatedID:
        print("ID: {}".format(id))
        session, whispermodel, seglen, bs, stride, index = id.split("_")

        index = int(index)
        bs = int(bs[2:])
        stride = int(stride[3:])

        print("Adding id {} to session {}".format(index, session))
        if(session in sessionToID):
            sessionToID[session].append((index, bs, stride))
        else:
            sessionToID[session] = [(index, bs, stride)]

    uniqueSessions = sorted(list(sessionToID.keys()))
    sessionToIndexToText = {}
    for uniqueSession in uniqueSessions:
        sessionToIndexToText[uniqueSession] = embeddingToText(os.path.join(args.path, uniqueSession, '{}.csv'.format(uniqueSession)))

    sessionToText = {}
    for session in sorted(list(sessionToID.keys())):
        sessionToText[session] = ""

        if(len(sessionToID[session]) <= 1):
            sessionToText[session] = sessionToIndexToText[session][sessionToID[session][0][0]]

        else:
            for i in range(len(sessionToID[session])-1):
                #grab the current and next session. Look for overlap. Remove if present.
                currentTup = sorted(sessionToID[session])[i]
                nextTup    = sorted(sessionToID[session])[i+1]

                if(nextTup[0] - currentTup[0] < currentTup[1]): #If the difference between indices is < the batch, we know there must be (some) overlap, so we should account for that...
                    howMuchOverlap = nextTup[0] - currentTup[0]

                    currentText = sessionToIndexToText[session][currentTup[0]]
                    currentLines = currentText.split("\n")

                    sessionToText[session] += "\n".join(currentLines[:howMuchOverlap])

                else:
                    sessionToText[session] += sessionToIndexToText[session][currentTup[0]] + '\n'

            sessionToText[session] += sessionToIndexToText[session][sorted(sessionToID[session])[-1][0]]

    #allText = []
    #relatedID = [int(i.split('_')[-1]) for i in relatedID]
    #for rid in relatedID:
    #    allText.append(e2t[rid])

    #print("Original Token Cnt: {}".format(estimateTokens("\n".join(allText))))
    #print("New Token Count: {}".format(sum([estimateTokens(sessionToText[i]) for i in sessionToText] )))
    #input()

    #for i in sessionToText:
    #    print("SESSION: {}".format(i))
    #    print(sessionToText[i])
    #    print("********************************************************\n\n")
    #    input()

    allText = "\n".join(sessionToText[i] for i in sessionToText)
    #print(allText)
    #input()

    print("Querying OpenAI using {} | {} Tokens...".format(args.model, estimateTokens(allText)))
    #print("\n".join(allText))
    response = openai.ChatCompletion.create(
        model=args.model,
        messages = [
            {'role':'system', 'content':'You are a Dungeons and Dragons AI'},
            {'role':'user', 'content':'Below is a query provided by the user. You should use the information provided further down to answer this query as well as possible.'},
            {'role':'user', 'content': args.query},
            {'role':'user', 'content': 'Below is the context provided. You will see a text transcript of a dungeons and dragons campaign. Each line is labeled with a speaker. Here are the speaker codes, names, and character / role:\n1) cro: Crossland (DM)\n2) let: Leticia (Russet Crow)\n3) ric: Richard (Likkvorn)\n4) sim: Simon (Lief) 5) ben: Ben (Oskar) 6) kacie: Kacie (Isra). Please read through what was said, and help with the query as best you can.'},
            #{'role':'user', 'content':"\n".join(allText)}
            {'role':'user', 'content':allText}
        ]
    )

    #print(response)
    print("\n\n\n~~~ Chat GPT Says ~~~")
    print(response['choices'][0]['message']['content'])
    

if (__name__ == "__main__"):
    main()