import json
import time
import tiktoken

import backoff
from openai import OpenAI, RateLimitError

client = OpenAI()

# basic test
def test():
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
        {"role": "user", "content": "Compose a poem that explains the concept of recursion in programming."}
        ]
    )

    print(completion.choices[0].message)


top_keep_fields = [
    "name",
    "numberOfGuests",
    "address",
    "roomType",
    "stars",
    "pricing",
    "bathroomLabel",
    "bedroomLabel",
    "roomTypeCategory",
    "guestControls",
    "priceDetails",
    "reviewDetailsInterface",
    "highlights",
    "listingExpectations",
]

object_keep_fields = {
    "sectionedDescription": [
        "access",
        "description",
        "name",
        "neighborhoodOverview",
        "space",
        "summary"
    ],
}

array_keep_fields = {
    "reviews": [
        "comments",
        "rating"
    ],
    "listingAmenities": [
        "description",
        "name",
        "isPresent"
    ],
}

ski_system_prompt = """You are a ski assistant, skilled in helping skiers find the perfect Airbnb for their ski trip.
You are given an AirBnB listing in JSON format and asked to rate it on a scale of 0 to 100, with 100 being the best. Please provide a list of reasons for your rating.
Provide your response in JSON format with structure like {"rating":4, "reasons": []}. You are given the following listing:
"""

review_system_prompt = """You are a ski assistant, skilled in helping skiers find the perfect Airbnb for their ski trip.
You are given an AirBnB listing in JSON format and asked to determine how many (if any) reviews mention skiing in a positive way.
Provide your response in JSON format with structure like ex. {"poitive_mentions": 4}. You are given the following listing:
"""

ski_system_prompt_2 = """You are a helpful rental property evaluator, skilled in deciding if an Airbnb property described in JSON is suitable for one of the following types of skiers:
- A family with children
- A group of friends
- A solo traveler
Please give your response in JSON with structure: {skierType: "family", rating: 4, reasons: []}. You are given the following listing:
"""

criteria = """
When choosing an Airbnb property for a ski trip, there are several factors to consider to ensure a comfortable and enjoyable stay. Here are some things to look for:

1. **Proximity to Ski Resorts:**
   - Check the distance to the ski resorts you plan to visit. A property that is close to the slopes can save you time and make transportation more convenient.

2. **Amenities:**
   - Look for amenities that cater to skiers, such as a ski storage area, heated boot racks, or a drying room for wet gear.

3. **Transportation:**
   - Consider the availability of public transportation or shuttle services to the ski resorts if you don't have your own vehicle.

4. **Heating and Insulation:**
   - Ensure that the property has reliable heating to keep you warm after a day on the slopes. Well-insulated windows and doors are also important to keep the cold out.

5. **Hot Tub or Fireplace:**
   - A property with a hot tub or a fireplace can provide a cozy and relaxing atmosphere, perfect for winding down after a day of skiing.

6. **Kitchen Facilities:**
   - Having a well-equipped kitchen can be a plus, allowing you to prepare meals and snacks, saving both time and money.

7. **Wi-Fi and Entertainment:**
   - Check for reliable Wi-Fi, especially if you need to stay connected. Additionally, having entertainment options like a TV, streaming services, or board games can enhance your downtime.

8. **Laundry Facilities:**
   - If you're planning an extended ski trip, having access to laundry facilities can be convenient for washing snow gear.

9. **Parking:**
   - If you're driving to the ski resort, make sure the property has adequate parking space, and check if there are any additional costs associated with parking.

10. **Reviews:**
    - Read reviews from previous guests, particularly those who visited for a ski trip. This can provide valuable insights into the property's suitability for winter activities.

11. **Safety Measures:**
    - Confirm that the property has safety features such as smoke detectors, carbon monoxide detectors, and a fire extinguisher.

12. **Local Services:**
    - Consider the proximity of the property to local amenities such as grocery stores, restaurants, and ski equipment rental shops.

By considering these factors, you can increase the likelihood of finding an Airbnb property that meets your needs and enhances your overall ski trip experience.
"""


def trim_listing(listing) -> dict:
    """
    Trim out fields that the LLM does not need
    """
    trimmed = {}
    for field in top_keep_fields:
        if not field in listing:
            continue
        trimmed[field] = listing[field]
    
    for field in object_keep_fields:
        trimmed[field] = {}
        for subfield in object_keep_fields[field]:
            if not subfield in listing[field]:
                continue
            trimmed[field][subfield] = listing[field][subfield]
    
    for field in array_keep_fields:
        trimmed[field] = []
        for item in listing[field]:
            trimmed_item = {}
            for subfield in array_keep_fields[field]:
                if not subfield in item:
                    continue
                trimmed_item[subfield] = item[subfield]
            trimmed[field].append(trimmed_item)
    
    return trimmed

def count_listing_tokens(trimmed_listing) -> int:
    """
    Count the number of tokens in a trimmed listing using the LLM tokenizer.
    """
    trimmed_json = json.dumps(trimmed_listing)
    enc = tiktoken.get_encoding('cl100k_base') #used by GTP3.5-Turbo and GPT4
    return len(enc.encode(trimmed_json))
    

def test_get_property_rating():
    listing_data = json.load(open("./dataset_airbnb-scraper_2023-10-26_23-44-51-570.json"))
    
    for listing in listing_data:
        trimmed = trim_listing(listing)
        
        print(f'getting property rating for: {trimmed["name"]} - {trimmed["address"]}')
        rating = get_ski_propterty_rating(trimmed)
        print(rating+ "\n")

def test_get_review_ski_mentions():
    listing_data = json.load(open("./dataset_airbnb-scraper_2023-10-26_23-44-51-570.json"))
    
    for listing in listing_data:
        trimmed = trim_listing(listing)
        
        print(f'getting review ski mentions for: {trimmed["name"]} - {trimmed["address"]}')
        mentions = get_review_ski_mentions(trimmed)
        print(mentions+ "\n")
        

@backoff.on_exception(backoff.expo, RateLimitError)
def get_ski_propterty_rating(listing):
    """
    Get a ski property rating from the LLM
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        response_format={ "type": "json_object" },
        messages=[
            {"role": "system", "content": ski_system_prompt_2},
            {"role": "user", "content": json.dumps(listing)},
        ]
    )
    return response.choices[0].message.content

@backoff.on_exception(backoff.expo, RateLimitError)
def get_review_ski_mentions(listing):
    """
    Get a ski property rating from the LLM
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        response_format={ "type": "json_object" },
        messages=[
            {"role": "system", "content": review_system_prompt},
            {"role": "user", "content": json.dumps(listing)},
        ]
    )
    return response.choices[0].message.content

def create_ski_assistant():
    """
    Create an OpenAI ski assistant
    """
    pass



test_get_property_rating()