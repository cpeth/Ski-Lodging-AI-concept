

from google.cloud import firestore
from google.cloud import secretmanager
import functions_framework
import os
import httpx

project_id = 'ski-geist-poc'
parent = f'projects/{project_id}'

db = firestore.Client(project=project_id)
client = secretmanager.SecretManagerServiceClient()

#TODO: move these back to OS env variables which Secret Manager can populate on deploy

auth_key_secret_id = 'api-master-key'
api_key_secret_id = 'apify-api-key'

auth_key_name = client.secret_version_path(project_id, auth_key_secret_id, 'latest')
auth_key_response = client.access_secret_version(name=auth_key_name)
auth_key = auth_key_response.payload.data.decode('UTF-8')

api_key_name = client.secret_version_path(project_id, api_key_secret_id, 'latest')
api_key_response = client.access_secret_version(name=api_key_name)
api_key = api_key_response.payload.data.decode('UTF-8')

def authenticate_request(request):
    """
    Authenticate the request to make sure it is coming from Apify via Bearer token
    """
    if not 'Authorization' in request.headers:
        print('no Authorization header')
        return False
    
    auth_header = request.headers['Authorization']
    request_key = auth_header.split(' ')[1]
    if not auth_key == request_key:
        print('invalid auth key')
        return False
    
    if not request.method == 'POST':
        print('invalid method')
        return False   

    return True

@functions_framework.http
def airbnb_success_request_handler(request):
    """
    Callback function for Apify airbnb success webhook when Apify finishes scraping. 
    Then function will make a request to the apify api to get the data and store it in firestore
    """
    if not authenticate_request(request):
        return 'Not Authorized', 401
    
    # get the run id from the request
    data = request.get_json()

    if data["eventType"] == "TEST":
        print('test event, aborting function')
        return 'OK', 200

    dataset_id = data['resource']['defaultDatasetId']
    call_timestmap = data['createdAt']

    print(f'retrieving data for dataset id: {dataset_id} at {call_timestmap}')

    # make a request to the apify api to get the dataset with httpx
    url = f'https://api.apify.com/v2/datasets/{dataset_id}/items?token={api_key}'
    response = httpx.get(url)
    response_data = response.json()

    # store the data in firestore
    batch = db.batch()
    for item in response_data:
        doc_ref = db.collection('airbnb').document(str(item['id']))
        print(f'adding {item["id"]} to firestore')
        batch.set(doc_ref, item)

    batch.commit()

    print('finished adding data to firestore')

    return 'OK', 200

@functions_framework.http
def auth_test_handler(request):
    """
    Test function to check if the auth key is working
    """
    if not authenticate_request(request):
        return 'Not Authorized', 401
    
    return 'OK', 200