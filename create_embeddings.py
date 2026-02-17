# pip install openai numpy

import os
import openai
import numpy as np

openai.api_key = os.environ.get("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

def get_embedding(text, model="text-embedding-3-large"):
    response = openai.embeddings.create(input=text, model=model)
    return response.data[0].embedding

# we will raplace this with our list of descriptions of the objects
descriptions = [
    "A tall object with three protruding arms and shiny surface.",
    "Looks like a tripod with thin rods and metallic finish."
]

embeddings = [get_embedding(desc) for desc in descriptions]

# Convert to numpy for later similarity calculations
embeddings = np.array(embeddings)
print("Shape of embeddings:", embeddings.shape)
