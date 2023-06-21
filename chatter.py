import openai 
import os 
import subprocess

from tokenizer import Tokenizer

openai.api_key = os.getenv('OPENAI_AUTH')

"""class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'"""


class Colorcodes(object):
    """
    Provides ANSI terminal color codes which are gathered via the ``tput``
    utility. That way, they are portable. If there occurs any error with
    ``tput``, all codes are initialized as an empty string.
    The provides fields are listed below.
    Control:
    - bold
    - reset
    Colors:
    - blue
    - green
    - orange
    - red
    :license: MIT
    """
    def __init__(self):
        try:
            self.bold = subprocess.check_output("tput bold".split()).decode('latin1')
            self.reset = subprocess.check_output("tput sgr0".split()).decode('latin1')

            self.blue = subprocess.check_output("tput setaf 4".split()).decode('latin1')
            self.green = subprocess.check_output("tput setaf 2".split()).decode('latin1')
            self.orange = subprocess.check_output("tput setaf 3".split()).decode('latin1')
            self.red = subprocess.check_output("tput setaf 1".split()).decode('latin1')
        except subprocess.CalledProcessError as e:
            self.bold = ""
            self.reset = ""

            self.blue = ""
            self.green = ""
            self.orange = ""
            self.red = ""



c = Colorcodes()


class Chatter():
    def __init__(self, model):
        self.model = model 
        self.tizer = Tokenizer(name=self.model)

    def passMessagesGetCompletion(self, messages):
        completion = openai.ChatCompletion.create(
                model=self.model ,
                messages= messages
            )
        
        return(completion)


    def chat(self, prompt=None, include_previous_replies=False, extra_messages=[], halt=False):
        messages = [] 
        total = 0 

        if(include_previous_replies and extra_messages):
            messages = extra_messages

        print(f"{c.bold} ~~ Chatting with {self.model} ~~{c.reset}")
        while True:
            if(not prompt):
                prompt = input(f"{c.blue}Prompt> {c.reset}")

            messages.append({'role':'user', 'content':prompt})

            tokens = self.tizer.calculate_tokens_from_messages(messages)
            price  = self.tizer.calculate_price_from_messages(messages)
            total += price 

            print("Tokens {} | Cost {:.4f} | Total {:.4f}".format(tokens, price, total))
            completion = self.passMessagesGetCompletion(messages)

            reply = completion.choices[-1].message.content 
            print("{}Reply> {}{}".format(c.green, reply, c.reset))

            if(not include_previous_replies):
                messages = [] 
            else:
                messages.append({'role':'assistant', 'content':'reply'})

            prompt=None


        
if(__name__ == "__main__"):
    chat = Chatter('gpt-4') 
    chat.chat(include_previous_replies=True)

