import json
import time
import tiktoken

import backoff
from openai import OpenAI, RateLimitError

client = OpenAI()

review_system_prompt = """You are a ski assistant, skilled in helping skiers find the perfect Airbnb for their ski trip.
You are given an arrray of reviews for an AirBnB listing in JSON format and asked to determine how many (if any) reviews mention skiing in a positive way and list the 0-based indexes of those review in the array.
Provide your response in JSON format with structure like ex. {"poitive_mentions": 4, "indexes": [0,3,6,8]}. You are given the following listing:
"""


def count_listing_tokens(trimmed_listing) -> int:
    """
    Count the number of tokens in a trimmed listing using the LLM tokenizer.
    """
    trimmed_json = json.dumps(trimmed_listing)
    enc = tiktoken.get_encoding('cl100k_base') #used by GTP3.5-Turbo and GPT4
    return len(enc.encode(trimmed_json))
    

def test_get_review_ski_mentions():
    listing_data = json.load(open("./dataset_airbnb-scraper_2023-10-26_23-44-51-570.json"))
    
    for listing in listing_data:
        reviews = []

        for review in listing["reviews"]:
            reviews.append(review["comments"])
        
        print(f'getting review ski mentions for: {listing["name"]} - {listing["address"]} - {listing["id"]}')
        mentions = get_review_ski_mentions(reviews)
        print(mentions+ "\n")

@backoff.on_exception(backoff.expo, RateLimitError)
def get_review_ski_mentions(reviews):
    """
    Get a ski property rating from the LLM
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        response_format={ "type": "json_object" },
        messages=[
            {"role": "system", "content": review_system_prompt},
            {"role": "user", "content": json.dumps(reviews)},
        ]
    )
    return response.choices[0].message.content


test_get_review_ski_mentions()