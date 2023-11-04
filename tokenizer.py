import tiktoken 

class Tokenizer:
    def __init__(self, name=None, use_tiktoken=True):
        self.model = name 
        self.use_tiktoken = use_tiktoken

        if(not self.model):
            print("[Tokenizer] No model given...")
            exit()

        self.model_costs = {
            "chatgpt": {"input": 0.0015, "output": 0.002, "window": 4096, "date": None},
            "chatgpt-4k": {"input": 0.0015, "output": 0.002, "window": 4096, "date": None},
            "chatgpt-16k": {"input": 0.003, "output": 0.004, "window": 16384, "date": None},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002, "window": 4096, "date": "Sep 2021"},
            "gpt-3.5-turbo-0613": {"input": 0.0015, "output": 0.002, "window": 4096, "date": "Sep 2021"},
            "gpt-3.5-turbo-16k": {"input": 0.003, "output": 0.004, "window": 16384, "date": "Sep 2021"},
            "gpt-4": {"input": 0.03, "output": 0.06, "window": 8192, "date": "Sep 2021"},
            "gpt-4-8k": {"input": 0.03, "output": 0.06, "window": 8192, "date": "Sep 2021"},
            "gpt-4-32k": {"input": 0.06, "output": 0.12, "window": 32768, "date": "Sep 2021"},
            "gpt-4-0613": {"input": 0.03, "output": 0.06, "window": 8192, "date": "Sep 2021"},
            "instructgpt-ada": {"input": 0.0004, "output": 0.0004, "window": None, "date": None},
            "instructgpt-babbage": {"input": 0.0005, "output": 0.0005, "window": None, "date": None},
            "instructgpt-curie": {"input": 0.002, "output": 0.002, "window": None, "date": None},
            "instructgpt-davinci": {"input": 0.02, "output": 0.02, "window": None, "date": None},
            "ft-ada": {"input": 0.0004, "output": 0.0016, "window": None, "date": None},
            "ft-babbage": {"input": 0.0006, "output": 0.0024, "window": None, "date": None},
            "ft-curie": {"input": 0.003, "output": 0.012, "window": None, "date": None},
            "ft-davinci": {"input": 0.03, "output": 0.12, "window": None, "date": None},
            "embeddings-ada-v2": {"input": 0.0001, "window": None, "date": None},
            "ada-002": {"input": 0.0004, "output": 0.0004, "window": None, "date": None},
            "embeddings-ada-v1": {"input": 0.004, "window": None, "date": None},
            "embeddings-babbage-v1": {"input": 0.005, "window": None, "date": None},
            "embeddings-curie-v1": {"input": 0.02, "window": None, "date": None},
            "embeddings-davinci-v1": {"input": 0.2, "window": None, "date": None},
            "image-1024x1024": {"price": 0.02, "window": None, "date": None},
            "img-1024": {"price": 0.02, "window": None, "date": None},
            "image-512x512": {"price": 0.018, "window": None, "date": None},
            "img-512": {"price": 0.018, "window": None, "date": None},
            "image-256x256": {"price": 0.016, "window": None, "date": None},
            "img-256": {"price": 0.016, "window": None, "date": None},
            "whisper": {"input": 0.006, "window": None, "date": None},
        }

        if(self.model):
            self.modelinfo = self.get_model_info(self.model)  

    def get_ppt(self, arg=None):
        if(not self.modelinfo):
            return(None)
        
        if(arg and arg in self.modelinfo):
            return(self.modelinfo[arg])
        
        if('input' in self.modelinfo):
            return(self.modelinfo['input'])
        
        if('price' in self.modelinfo):
            return(self.modelinfo['price'])


    def calculate_tokens(self, string):
        if(self.use_tiktoken):
            encoding = tiktoken.get_encoding('cl100k_base')
            return(len(encoding.encode(string)))

        else:
            token_count = len(string) / 4  # Divide string length by 4, rounded up
            return token_count
    
    def calculate_tokens_from_messages(self, messages):
        s = ""
        for msg in messages:
            content = msg['content']
            s += content 

        return(self.calculate_tokens(s))

    def calculate_price(self, string, arg=None):
        token_count = self.calculate_tokens(string)
        price = (token_count / 1000.) * self.get_ppt(arg)
        return price
    
    def calculate_price_from_tokens(self, tokens, arg=None):
        price = (tokens / 1000.) * self.get_ppt(arg)
        return(price)

    def calculate_price_from_messages(self, messages):
        tokens = self.calculate_tokens_from_messages(messages)

        price = self.calculate_price_from_tokens(tokens)
        return(price)

    def get_model_info(self, model_name):
        model_name = model_name.lower()
        if model_name in self.model_costs:
            return self.model_costs[model_name]
        else:
            return None

    def print_available_models(self):
        print("Available Models:")
        for model_name, costs in self.model_costs.items():
            if "input" in costs and "output" in costs:
                print(f"{model_name}: Input cost - ${costs['input']}/1K tokens, Output cost - ${costs['output']}/1K tokens")
            elif "usage" in costs:
                print(f"{model_name}: Usage cost - ${costs['usage']}/1K tokens")
            elif "price" in costs:
                print(f"{model_name}: Price - ${costs['price']}")