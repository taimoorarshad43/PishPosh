import requests
import base64
from mistralai import Mistral
import os

def getimages():
    # Calling API for random image
    img_url = 'https://picsum.photos/200'

    img_data = requests.get(img_url).content

    # Getting the base64 string
    # img_data_encoded = base64.b64encode(img_data).decode('utf-8')
    img_data_encoded = base64.b64encode(img_data)

    return img_data_encoded

base64_image = getimages()

# Retrieve the API key from environment variables
api_key = os.environ["MISTRAL_API_KEY"]

# Specify model
model = "pixtral-12b-2409"

# Initialize the Mistral client
client = Mistral(api_key=api_key)


def getproductdescription(image_data):

    """Function that takes base64 utf-8 image data and returns an image description from Mistral's AI"""

    # Define the messages for the chat
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Give me a short product description for this picture that is a title of 5-12 words."
                },
                {
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{image_data}" 
                }
            ]
        }
    ]

    # Get the chat response
    chat_response = client.chat.complete(
        model=model,
        messages=messages
    )

    # Print the content of the response and return as output
    print(chat_response.choices[0].message.content)

    output = chat_response.choices[0].message.content

    return output