import os
import json
import hashlib

from openai import OpenAI
from google.cloud import firestore
from google.cloud import secretmanager
import functions_framework

project_id = 'ski-geist-poc'
parent = f'projects/{project_id}'

db = firestore.Client(project=project_id)
secret_client = secretmanager.SecretManagerServiceClient()

#TODO: move these back to OS env variables which Secret Manager can populate on deploy

auth_key_secret_id = 'api-master-key'
open_ai_secret_id = 'openai-api-key'

auth_key_name = secret_client.secret_version_path(project_id, auth_key_secret_id, 'latest')
auth_key_response = secret_client.access_secret_version(name=auth_key_name)
auth_key = auth_key_response.payload.data.decode('UTF-8')

api_key_name = secret_client.secret_version_path(project_id, open_ai_secret_id, 'latest')
api_key_response = secret_client.access_secret_version(name=api_key_name)
api_key = api_key_response.payload.data.decode('UTF-8')

os.environ["OPENAI_API_KEY"] = api_key
openai_client = OpenAI()

review_system_prompt = """You are a ski assistant, skilled in helping skiers find the perfect Airbnb for their ski trip.
You are given an arrray of reviews for an AirBnB listing in JSON format and asked to determine how many (if any) reviews mention skiing in a positive way and list the 0-based indexes of those review in the array.
Provide your response in JSON format with structure like ex. {"poitive_mentions": 4, "indexes": [0,3,6,8]}. You are given the following listing:
"""

def hash_review_content(review_body):
    return hashlib.sha256(review_body.encode()).hexdigest()

def get_doc_from_firestore(collection, doc_id):
    doc_ref = db.collection(collection).document(doc_id)
    doc = doc_ref.get()
    return doc

def save_result_to_firestore(collection, data):
    id = hash_review_content(data['review_body'])
    doc_ref = db.collection(collection).document(id)
    doc_ref.set(data)


def authenticate_request(request):
    """
    Authenticate the request to make sure it is coming from Cloud Task via Bearer token
    """
    if not 'Authorization' in request.headers:
        return False
    
    auth_header = request.headers['Authorization']
    request_key = auth_header.split(' ')[1]
    if not auth_key == request_key:
        return False
    
    if not request.method == 'POST':
        return False   

    return True

def get_review_ski_mentions(reviews):
    """
    Get a ski property rating from the LLM
    """

    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        response_format={ "type": "json_object" },
        messages=[
            {"role": "system", "content": review_system_prompt},
            {"role": "user", "content": json.dumps(reviews)},
        ]
    )
    return json.loads(response.choices[0].message.content)

@functions_framework.http
def openai_review(request):
    """
    Callback function for Cloud Task to call the OpenAI API to get the review ski mentions
    """
    if not authenticate_request(request):
        return 'Not Authorized', 401
    
    # get the run id from the request
    data = request.get_json()
    document_id = data['document_id']

    print(f'getting review ski mentions for: {document_id}')

    if 'test' in document_id:
        print('test event, aborting function')
        return 'OK', 200

    listing = get_doc_from_firestore('airbnb', document_id).to_dict()
    reviews = []

    for review_body in listing["reviews"]:
        reviews.append(review_body["comments"])
    
    mentions = get_review_ski_mentions(reviews)

    if mentions['positive_mentions'] == 0 or 'indexes' not in mentions:
        print('no positive mentions found')
        print(json.dumps(mentions))
        return 'OK', 200
    
    for index in mentions['indexes']:
        review_body = listing["reviews"][index]['comments']
        rating = listing["reviews"][index]['rating']

        doc = {
            "parent_id": document_id,
            "address": listing["address"],
            "rating": rating,
            "review_body": review_body,
            "url": f'https://www.airbnb.com/rooms/{listing["id"]}'
        }

        save_result_to_firestore('airbnb-reviews', doc)

    return 'OK', 200