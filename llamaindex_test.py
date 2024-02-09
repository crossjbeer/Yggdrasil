import llama_index as lindx 

import os 
os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_AUTH")

from llama_index import VectorStoreIndex, SimpleDirectoryReader

documents = SimpleDirectoryReader("./notes").load_data()
index = VectorStoreIndex.from_documents(documents)

query_engine = index.as_query_engine()
#print(query_engine.query("Please tell me about timberhold."))
print(query_engine.query('What are the rules of the spell fireball? '))