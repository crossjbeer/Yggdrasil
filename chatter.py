from openai import OpenAI
import os 
import datetime as dt 

from tokenizer import Tokenizer
from colorcodes import Colorcodes 

#openai.api_key = os.getenv('OPENAI_AUTH')

c = Colorcodes()


class Chatter():
    def __init__(self, model, logfile=None):
        self.model = model 
        self.tizer = Tokenizer(name=self.model)

        self.logfile = logfile 
        self.log=None
        self.log = self.getLog(self.logfile)

        self.client = OpenAI(api_key=os.environ.get("OPENAI_AUTH"))

    def getFuncNameFromResponse(self, response):
        return(response['function_call']['name'])
    
    def getFunctionArgsResponse(self, response):
        import json 
        return(json.loads(response['function_call']['arguments']))

    def passMessagesGetCompletion(self, messages, functions=[]):
        chat_completion = self.client.chat.completions.create(
                        messages=messages,
                        model=self.model)
        
        return(chat_completion)
    
    def getUsrMsg(self, message):
        return({'role':'user', 'content':message})
    
    def getAssMsg(self, message):
        return({'role':'assistant', 'content':message})
    
    def getSysMsg(self, message):
        return({'role':'system', 'content':message})
    
    def passMessagesGetReply(self, messages, functions=[]):
        completion = self.passMessagesGetCompletion(messages, functions)

        return(completion.choices[-1].message.content)
    
    def getLog(self, logfile=None):
        if(self.log is not None):
            return(self.log)

        log = None 
        if(not logfile):
            try:
                if('chat.log' in os.listdir('./')):
                    log = open('./chat.log', 'a')
                else:
                    log = open('./chat.log', 'w')

            except Exception as e: 
                print("No Log File Provided. Failed to open default log file...")
                print(e)
                exit()

        else:
            if(os.path.isfile(logfile)):
                log = open(logfile, 'a')
            else:
                log = open(logfile, 'w')

        return(log)
    
    def writeMsg(self, msg, log=None):
        if(not log):
            log = self.log

        log.write(f"{msg['role']}: {msg['content']}\n")    

        return()    

    def printMsg(self, msg, halt=False):
        print(c.pblue('*'), c.pbold(msg['role']))
        print()
        print(c.pblue("*"), c.pred(msg['content']))

        if(halt):
            input('Waiting...')   

    def printMessages(self, messages, halt=False):
        for i, msg in enumerate(messages):
            print(c.pblue('********************************\n* Message {:<10}'.format(i+1)))

            self.printMsg(msg, halt)
            print()

        return() 
    
    def startupLog(self, startupMsg, log=None):
        if(not log):
            log = self.log 

        log.write(f"""\n\n
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
~~~ New Chat {dt.datetime.now()} | {self.model} ~~~\n""")


        if(len(startupMsg)):
            for msg in startupMsg:
                self.writeMsg(msg, log)

        return()        
    
    def toolChat(self, prompt=None, extra_messages=[], halt=False):
        self.getlog()

        total = 0 
        messages = [] 
        if(extra_messages):
            messages = extra_messages

        self.startupLog(messages, self.log)

        while True:
            if(not prompt):
                prompt = self.usrprompt()

    def usrprompt(self):
        return(input(f"{c.blue}Prompt> {c.reset}"))

    def chat(self, prompt=None, include_previous_replies=False, extra_messages=[], halt=False):
        self.getLog()

        total = 0
        messages = []  

        if(include_previous_replies and extra_messages):
            messages = extra_messages

        self.startupLog(extra_messages, self.log)

        print(f"\n{c.bold} ~~ Chatting with {self.model} ~~{c.reset}\n")
        while True:
            if(not prompt):
                prompt = self.usrprompt()

            messages.append({'role':'user', 'content':prompt})

            self.writeMsg(messages[-1], self.log)

            tokens = self.tizer.calculate_tokens_from_messages(messages)
            price  = self.tizer.calculate_price_from_tokens(tokens, self.model)
            total += price 

            print("{}Tokens>{} {} | Cost {:.4f} | Total ${:.4f}".format(c.orange, c.reset, tokens, price, total))
            completion = self.passMessagesGetCompletion(messages)

            reply = completion.choices[-1].message.content 

            tokens = self.tizer.calculate_tokens_from_messages([{'role':'assistant', 'content':reply}])
            price  = self.tizer.calculate_price_from_tokens(tokens, 'output')
            total += price

            print("{}Reply> {}{}".format(c.green, reply, c.reset))
            print("{}Tokens>{} {} | Cost {:.4f} | Total ${:.4f}".format(c.orange, c.reset, tokens, price, total))

            if(not include_previous_replies):
                messages = [] 
            else:
                messages.append({'role':'assistant', 'content':reply})

            self.writeMsg({'role':'assistant', 'content':reply}, self.log)    
            prompt=None

    def chat_db(self, prompt=None, include_previous_replies=False, extra_messages=[], halt=False, host='localhost', port='', user='crossland', password='pass', database='yggdrasil'):
        from postgre_chat import connect, start_chat, append_message
        connection = connect(host, port, user, password, database)
        
        total = 0

        messages = []  
        if(include_previous_replies and extra_messages):
            messages = extra_messages

        print(f"\n{c.bold} ~~ Chatting with {self.model} ~~{c.reset}\n")

        first_run = True 
        while True:
            if(not prompt):
                prompt = self.usrprompt()

            if(first_run):
                chat_id = start_chat(connection, prompt, role='user')
                first_run=False

                if(messages):
                    for msg in messages:
                        append_message(connection, chat_id, msg['content'], msg['role'])
            else:
                append_message(connection, chat_id, prompt, 'user')

            messages.append({'role':'user', 'content':prompt})

            tokens = self.tizer.calculate_tokens_from_messages(messages)
            price  = self.tizer.calculate_price_from_tokens(tokens, self.model)
            total += price 

            print("{}Tokens>{} {} | Cost {:.4f} | Total ${:.4f}".format(c.orange, c.reset, tokens, price, total))
            completion = self.passMessagesGetCompletion(messages)

            reply = completion.choices[-1].message.content 

            tokens = self.tizer.calculate_tokens_from_messages([{'role':'assistant', 'content':reply}])
            price  = self.tizer.calculate_price_from_tokens(tokens, 'output')
            total += price

            print("{}Reply> {}{}".format(c.green, reply, c.reset))
            print("{}Tokens>{} {} | Cost {:.4f} | Total ${:.4f}".format(c.orange, c.reset, tokens, price, total))

            append_message(connection, chat_id, reply, 'assistant')

            if(not include_previous_replies):
                messages = [] 
            else:
                messages.append({'role':'assistant', 'content':reply})

            self.writeMsg({'role':'assistant', 'content':reply}, self.log)    
            prompt=None

    """
    def tool_chat(self, prompt=None, extra_messages=[], tools={}, halt=False):
        self.getLog()

        total = 0 
        messages = [] 
        if extra_messages:
            messages = extra_messages

        self.startupLog(messages, self.log)

        while True:
            if not prompt:
                prompt = self.usrprompt()

            messages.append({'role': 'user', 'content': prompt})
            self.writeMsg(messages[-1], self.log)

            tokens = self.tizer.calculate_tokens_from_messages(messages)
            price = self.tizer.calculate_price_from_tokens(tokens)
            total += price 

            print("Tokens {} | Cost {:.4f} | Total {:.4f}".format(tokens, price, total))

            # Get completion from ChatGPT
            tool_msg = messages 
            messages.append({'role':'user', 'content':'Above is a question from the user. Before answering, please use one or more tools to gather appropriate information'})

            completion = self.passMessagesGetCompletion(messages)

            # Extract the reply from ChatGPT
            reply = completion.choices[-1].message.content 
            print("{}Reply> {}{}".format(c.green, reply, c.reset))

            # Add the reply to the messages
            messages.append({'role': 'assistant', 'content': reply})
            self.writeMsg({'role': 'assistant', 'content': reply}, self.log)

            # Evaluate tools for the given reply
            tool_results = {}
            for tool_name, tool_data in tools.items():
                tool_prompt = f"Using tool {tool_name}: {tool_data['description']}"

                # Ask ChatGPT to evaluate the tool
                tool_evaluation_msg = f"{prompt} {tool_prompt}"
                tool_completion = self.passMessagesGetCompletion(messages + [{'role': 'user', 'content': tool_evaluation_msg}])

                # Extract the reply from ChatGPT for tool evaluation
                tool_reply = tool_completion.choices[-1].message.content

                # Store tool evaluation result
                tool_results[tool_name] = tool_reply

            # Print tool results
            print("Tool Results:")
            for tool_name, result in tool_results.items():
                print(f"{tool_name}: {result}")

            prompt = None    
        """


 