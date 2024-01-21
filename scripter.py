import pandas as pd 
import re 
import psycopg2


from nltk.corpus import stopwords 
from nltk.tokenize import word_tokenize

from tokenizer import Tokenizer 

CONTRACTIONS = { 
"ain't": "am not",
"aren't": "are not",
"can't": "cannot",
"can't've": "cannot have",
"'cause": "because",
"could've": "could have",
"couldn't": "could not",
"couldn't've": "could not have",
"didn't": "did not",
"doesn't": "does not",
"don't": "do not",
"hadn't": "had not",
"hadn't've": "had not have",
"hasn't": "has not",
"haven't": "have not",
"he'd": "he would",
"he'd've": "he would have",
"he'll": "he will",
"he'll've": "he will have",
"he's": "he is",
"how'd": "how did",
"how'd'y": "how do you",
"how'll": "how will",
"how's": "how is",
"I'd": "I would",
"I'd've": "I would have",
"I'll": "I will",
"I'll've": "I will have",
"I'm": "I am",
"I've": "I have",
"isn't": "is not",
"it'd": "it would",
"it'd've": "it would have",
"it'll": "it will",
"it's": "it is",
"let's": "let us",
"ma'am": "madam",
"mayn't": "may not",
"might've": "might have",
"mightn't": "might not",
"mightn't've": "might not have",
"must've": "must have",
"mustn't": "must not",
"mustn't've": "must not have",
"needn't": "need not",
"needn't've": "need not have",
"o'clock": "of the clock",
"oughtn't": "ought not",
"oughtn't've": "ought not have",
"shan't": "shall not",
"sha'n't": "shall not",
"shan't've": "shall not have",
"she'd": "she would",
"she'd've": "she would have",
"she'll": "she will",
"she's": "she is",
"should've": "should have",
"shouldn't": "should not",
"shouldn't've": "should not have",
"so've": "so have",
"that'd": "that would",
"that's": "that is",
"there'd": "there would",
"there'd've": "there would have",
"there's": "there is",
"they'd": "they would",
"they'd've": "they would have",
"they'll": "they will",
"they're": "they are",
"they've": "they have",
"to've": "to have",
"wasn't": "was not",
"we'd": "we would",
"we'd've": "we would have",
"we'll": "we will",
"we'll've": "we will have",
"we're": "we are",
"we've": "we have",
"weren't": "were not",
"what'll": "what will",
"what're": "what are",
"what's": "what is",
"what've": "what have",
"when's": "when is",
"when've": "when have",
"where'd": "where did",
"where's": "where is",
"where've": "where have",
"who'll": "who will",
"who's": "who is",
"who've": "who have",
"why's": "why is",
"why've": "why have",
"will've": "will have",
"won't": "will not",
"won't've": "will not have",
"would've": "would have",
"wouldn't": "would not",
"y'all": "you all",
"you'd": "you would",
"you'll": "you will",
"you're": "you are",
"you've": "you have"
}

NAMEDICT = {
    'cro':'<1>',
    'crossland':'<1>',
    'ric':'<2>',
    'richard':'<2>',
    'Richard':'<2>',
    'let':'<3>',
    'leticia':'<3>',
    'sim':'<4>',
    'simon':'<4>',
    'ben':'<5>',
    'kacie':'<6>',
    'casey':'<6>',
    'Leticia':'<3>'
}


class Scripter:
    def __init__(self, no_tokenizer_autoload=False, default_embedder='ada-002'):
        self.csv_path = "" 
        self.txt_path = ""

        self.host = ""
        self.database = ""
        self.table = ""
        self.user = ""
        self.password = ""
        self.connection = None 

        self.model = None 
        self.tizer = None 

        if(not no_tokenizer_autoload):
            self.loadTokenizer(default_embedder)

    def loadTokenizer(self, model):
        self.model = model
        self.tizer = Tokenizer(self.model)
        return(self.tizer)

    def loadTxt(self, path, parseOnSentence=False, sentence_delim=['.', '?', '!']):
        self.txt_path = path 

        txt = open(path, 'r')
        lines = txt.readlines() 

        sentences = []
        for line in lines:
            if not line.strip():
                continue

            if parseOnSentence:
                current_sentence = ""
                for char in line:
                    if char in sentence_delim:
                        if current_sentence:
                            sentences.append(current_sentence.strip()+'\n')
                        current_sentence = ""
                    else:
                        current_sentence += char
                if current_sentence:
                    sentences.append(current_sentence.strip())
            else:
                sentences.append(line)

        df = pd.DataFrame(sentences, columns=['text'])
        return df


    def loadCSV(self, path, *args, **kwargs):
        self.csv_path = path 

        df = pd.read_csv(self.csv_path, *args, **kwargs)

        return df
    
    def connectPostgreSQL(self, host, db, user, password):
        try:
            connection = psycopg2.connect(
                user=user,
                password=password,
                host=host,
                database=db
            )
    
        except Exception as e:
            print("PostgreSQL Connection Failed: [{}]".format(e))
            print(e)
            return(None)
        
        self.connection = connection 
        return(connection)
    
    def connectMySQL(self, host, db, user, password):
        try:
            connection = mysql.connector.connect(
                host=host,
                database=db,
                user=user,
                password=password
            )
        except Exception as e:
            print("Failed to connect to MySQL")
            print(e)
            return(None)
        
        self.connection = connection
        return(connection)

    def loadMySQL(self, table, argDict={}):
        connection = self.connection

        if(connection is None):
            print("No MySQL Connection")
            exit()

        cursor = connection.cursor()
        query = "SELECT start, end, class, text, session, session_name, session_id FROM {}".format(table)

        if(len(argDict)):
            for i, k in enumerate(argDict):
                if(isinstance(argDict[k], list)):
                    print("not list")

                    prepList = ["'{}'".format(lv) for lv in argDict[k]]
                    if(not i):
                        query += f" WHERE {k} IN " + "(" + ",".join(prepList) + ")"
                    else:
                        query += f" AND {k} IN " + '(' + ",".join(prepList) + ")"
                else:
                    if(not i):
                        query += f" WHERE {k} = '{argDict[k]}'"
                    else:
                        query += f" AND {k} = '{argDict[k]}'"

        query += ';'

        cursor.execute(query)
        result = cursor.fetchall()

        columns = ['start', 'end', 'class', 'text', 'session', 'session_name' ,'session_id']
        df = pd.DataFrame(result, columns=columns)

        sorted_df = df.sort_values(by=['session', 'session_id'])
        #grouped_df = sorted_df.groupby('session_name')
        #print(grouped_df)

        #for name, group in grouped_df:
        #    print(f"Session Name: {name}")
        #    print(group)
        #    print()

        #input()

        cursor.close()
        connection.close()

        return(df)
    
    def filterTranscript(self, df):
        self.filterFillerLines(df)
        return(df)
    
    def getStrRows(self, df, i, bs, cols=['text']):
        rows = self.getDFRows(df, i, bs, cols)

        strings = [] 
        for i, row in rows.iterrows():
            strings.append('| '.join([str(i) for i in row]))

        return(strings)

    def getDFRows(self, df, i, bs, cols=['text']):
        df = df[cols]

        if(bs == -1):
            return(df.iloc[i:])
        
        return(df.iloc[i:min(len(df)-1, i+bs)])

    def calcTokens(self, s, costcoeff = None):
        if(self.tizer):
            return(self.tizer.calculate_tokens(s))
        elif(costcoeff):
            return((len(s)/4)*costcoeff)
        return(None)

    def getClassTextList(self, df):
        return(list(zip(df['class'], df['text'])))

    def getClassTextRows(self, df, i, bs):
        subset = self.getDFRows(df, i, bs)
        rows = self.getClassTextList(subset)
        return(rows)
    
    def getClassTextStrRows(self, df, i, bs):
        subset = self.getDFRows(df, i, bs)
        rows = self.getClassTextList(subset)
        strRows = [": ".join(r) for r in rows]
        return(strRows)
    

    def getAllTokenChunkBounds(self, df, tokenCost, filter=False, cols=['text'], lag=0):
        """
        This function is responsible for learning the token chunk boundaries on some text-holding dataframe, given some 'tokenCost' limit. 

        Params: 
        - df (Dataframe): The dataframe holding the text to be chunked
        - tokenCost (int): The token limit per chunk
        - filter (bool): Whether or not to filter out filler words
        - cols (list): The columns to be used for chunking
        - lag (int): The lag between token chunks (any value > 0 will result in overlapping chunks and less certainty of the tokens/ chunk)

        Returns:
        - token_bounds (list): A list of tuples representing the token chunk boundaries
        """

        cumulative_tokens = 0
        current_bound_start = 0
        token_bounds = []

        # Iterate through each row in the dataframe
        for i, row in df.iterrows():
            # Calculate tokens for the current row
            line_tokens = self.calcTokens(row['text'])

            # Check if adding line_tokens exceeds the token limit
            if cumulative_tokens + line_tokens > tokenCost:
                # Note the token bound when the limit is exceeded
                token_bounds.append((max(0, current_bound_start-lag), i))

                cumulative_tokens = line_tokens 
                current_bound_start = i 
            else:
                # Update cumulative_tokens if the limit is not exceeded
                cumulative_tokens += line_tokens

        # Check if there are remaining rows after the last token bound
        if current_bound_start < len(df):
            token_bounds.append((max(0,current_bound_start-lag), len(df) - 1))

        return token_bounds
    
    def splitDFIntoTokenChunks(self, df, tokenCost, filter=False, cols=['text'], lag=0):
        token_bounds = self.getAllTokenChunkBounds(df, tokenCost, filter, cols, lag)

        chunks = []
        for i, j in token_bounds:
            chunks.append(self.getDFRows(df, i, j-i, cols))

        return(chunks)
    
    def tokenChunks(self, df, tokenCost, filter=False, cols=['text'], lag=0):
        token_bounds = self.getAllTokenChunkBounds(df, tokenCost, filter, cols, lag)

        chunks = []
        for i, j in token_bounds:
            #chunks.append(self.getDFRows(df, i, j-i, cols))
            chunks.append(self.getText(self.getDFRows(df, i, j-i, cols)))

        return(chunks)


    def combineRowList(self, row_list, name_dict={}):
        combined_text = ''  # Initialize an empty string for combined text
        current_speaker = None  # Initialize a variable to track the current speaker
        
        for speaker_class, text in row_list:
            if speaker_class != current_speaker:
                for_str_class = speaker_class 
                if(speaker_class in name_dict):
                    for_str_class = name_dict[speaker_class]
                combined_text += '\n' + str(for_str_class) + ": " + text
                current_speaker = speaker_class
            else:
                combined_text += ' ' + text
                
        return combined_text

    def filterFillerLines(self, df):
        with open('fillerlang.txt', 'r') as filler_file:
            self.filler_lang = [i.strip() for i in filler_file.read().splitlines()]

        df['text'] = df['text'].apply(self._preprocessText)
        df = df[~df['text'].isin(self.filler_lang)]

        df = df.reset_index()

    @staticmethod
    def _preprocessText(text):
        text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
        text = text.replace("'", "").replace(",", "")  # Remove apostrophes and commas
        text = text.replace("...", "")  # Remove ellipses
        text = text.lower()
        text = text.strip()
 
        return text
    
    def getTotalCharacterCount(self, df):
        total_count = 0

        for text in df['text']:
            total_count += len(text)

        return total_count
    
    def printText(self, df):
        for i, txt in enumerate(df.text):
            print(str(i) + '.', txt)

    def getText(self, df):
        txt = "" 
        for t in df.text:
            txt += t

        return(txt)
    
    def cleanText(self, text, anon=True, lower=True, stripper=True, contractions=True, punct=True, stopword=False, namedict=None):
        if(lower):
            text = text.lower()

        if(stripper):
            text = text.strip()

        if(contractions):
            text = " ".join([i if i not in CONTRACTIONS else CONTRACTIONS[i] for i in text.split(" ")])

        if(punct):
            text = re.sub('[^A-Za-z0-9]+', ' ', text)

        if(anon and namedict):
            text = self.anonymizeText(text, namedict)

        if(stopword):
            swords = set(stopwords.words('english'))
            tokens = word_tokenize(text)
            filtered_sentence = [w for w in tokens if w not in swords]
            text = " ".join(filtered_sentence)

        return(text)
    
    def cleanClass(self, cl, namedict):
        if(cl in namedict):
            return(namedict[cl])
        return('na')


    def cleanDFPipe(self, df, anon=True, lower=True, stripper=True, contractions=True, punct=True, stopword=False, namedict=NAMEDICT):
        if(df is None):
            print("No Dataframe...")
            exit()

        for i in range(len(df)):
            text = df.text.iloc[i]    
            text = self.cleanText(text, anon, lower, stripper, contractions, punct, stopword, namedict)
            df.loc[df.index == i, 'text'] = text

            if('class' in df.columns):
                cl = df['class'].iloc[i]
                cl = self.cleanClass(cl, namedict)
                df.loc[df.index == i, 'class'] = cl

        return(df)

    def anonymizeText(self, text, namedict=NAMEDICT):
        text = ' '.join([i if i not in namedict else namedict[i] for i in text.split(' ')])

        return(text)
    
    def anonymizeDF(self, df, namedict=NAMEDICT):
        for i in range(len(df)):
            text = df.text[i]

            text = self.anonymizeText(text, namedict=namedict)
            cl = self.cleanClass(cl, namedict)

            df.loc[df.index == i, 'text'] = text
            df.loc[df.index == i, 'class'] = cl

        return(df)
    
    def parseCategoriesFromInfoDoc(self, df, category_key='Category'):
        import re 
        all_categories = [] 
        for i, line in df.iterrows():
            if(re.search(category_key, line['text'])):
                category = line['text'].split(': ')[1].strip()
                all_categories.append(category)

        return(all_categories)
    
    def parseCategoriesAndInfoFromInfoDoc(self, df, category_key='Category'):
        import re 
        categories = {}

        category = None 
        information = [] 
        for i, line in df.iterrows():
            if(re.search(category_key, line['text'])):
                if(information is not None and category is not None):
                    for info in information:
                        categories[category].append(info)

                    information = []    
                    category = None

                category = line['text'].split(': ')[1].strip()
                if(category not in categories):
                    categories[category] = []
                    
            elif(category is not None):
                information.append(line['text'])

        if(information is not None and category is not None):
            for info in information:
                categories[category].append(info)

        return(categories)


def jaccard_distance(list_of_strings, input_string):
    def get_word_set(string):
        # Helper function to convert a string into a set of words
        return set(string.split())

    input_word_set = get_word_set(input_string)
    distances = []

    for string in list_of_strings:
        string_word_set = get_word_set(string)
        intersection = len(input_word_set.intersection(string_word_set))
        union = len(input_word_set.union(string_word_set))
        jaccard_distance = 1.0 - intersection / union
        distances.append(jaccard_distance)

    return distances

def main():
    tizer = Tokenizer(name='gpt-4')

    script = Scripter()

    #script.connectMySQL('localhost', 'yggdrasil', 'ygg', '')
    #df = script.loadMySQL('transcript', {'session':['20230406']})

    df = script.loadTxt('./notes/sessionnotes.txt')
    df = script.cleanDFPipe(df)

    query = """
    make up a story about lord nethergloom and liren meadowkin. 
    """

    chunks = []
    for i in range(0, len(df), 10):
        chunk = script.getStrRows(df, i, 10)

        chunk = '\n'.join(chunk)

        dist = jaccard_distance([chunk], query)

        chunks.append((dist, chunk))

    chunks = sorted(chunks, key=lambda x: x[0])
    for i in chunks[:10]:
        print(i)

def main1():
    script = Scripter() 
    script.loadTokenizer('ada-002')

    df = script.loadTxt('./phb/PH.txt', parseOnSentence=True)
    note_chunks = script.splitDFIntoTokenChunks(df, 1000, lag=0)

    for i, chunk in enumerate(note_chunks):
        chunk_tok = 0
        chunk_tok_vals=[]
        for i, row in chunk.iterrows():
            tokens = script.tizer.calculate_tokens(row['text'])
            chunk_tok += tokens 
            chunk_tok_vals.append(tokens)

        chunk['tokens'] = chunk_tok_vals

        if(chunk_tok > 1099):
            print("Chunk {}".format(i))
            print(chunk)
            print("TOO MANY TOKENS: {}".format(chunk_tok))
            
            input()
    
    tokens = [] 
    chars = [] 
    for i, line in df.iterrows():
        text = line['text']
        tok = script.tizer.calculate_tokens(text)

        tokens.append(tok)
        chars.append(len(text))

    df['tokens'] = tokens
    df['chars'] = chars

    print(df)

    print("MAX: {}".format(max(tokens)))
    print("MIN: {}".format(min(tokens)))
    print("AVG: {}".format(sum(tokens)/len(tokens)))
    print("MED: {}".format(sorted(tokens)[len(tokens)//2]))


if __name__ == "__main__":
    main1()

