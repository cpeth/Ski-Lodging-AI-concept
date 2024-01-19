import json
import os

from cloudevents.http import CloudEvent
import functions_framework

from google.events.cloud import firestore

from google.cloud import tasks_v2
from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()

project = 'ski-geist-poc'
location = 'us-west1'
queue = os.environ.get('CLOUD_TASKS_QUEUE', '')

auth_key_secret_id = 'api-master-key'

auth_key_name = client.secret_version_path(project, auth_key_secret_id, 'latest')
auth_key_response = client.access_secret_version(name=auth_key_name)
auth_key = auth_key_response.payload.data.decode('UTF-8')

@functions_framework.cloud_event
def handle_firestore_event(cloud_event: CloudEvent) -> None:
    """
    Triggers by a new AirBnB listing being added to the Firestore database.
    The document ID is passed to a Cloud Task to be processed by a consumer that
    calls the openAI API to extract review with positive mention of skiing.

    Args:
        cloud_event: cloud event with information on the firestore event trigger
    """
    firestore_payload = firestore.DocumentEventData()
    firestore_payload._pb.ParseFromString(cloud_event.data)

    print(f"Function triggered by change to: {cloud_event['source']}")
    

    # Extract the necessary information from the event
    document_id = firestore_payload.value.name.split('/')[-1]

    print(f"Changed document: {document_id}")
    
    if not queue:
        print('No queue specified, aborting function')
        return
    
    # Create a Cloud Tasks client
    client = tasks_v2.CloudTasksClient()

    # Define the Cloud Task payload
    task_payload = {
        'document_id': document_id,
    }

     # Construct the task.
    task = tasks_v2.Task(
        http_request=tasks_v2.HttpRequest(
            http_method=tasks_v2.HttpMethod.POST,
            url='https://us-west1-ski-geist-poc.cloudfunctions.net/openai_review',
            headers={"Content-type": "application/json", 'Authorization': f'Bearer {auth_key}'},
            body=json.dumps(task_payload).encode(),
        ),
        name=(
            client.task_path(project, location, queue, document_id)
        ),
    )

    created_task = client.create_task(
        tasks_v2.CreateTaskRequest(
            # The queue to add the task to
            parent=client.queue_path(project, location, queue),
            # The task itself
            task=task,
        )
    )

    print(f"Created task {created_task.name}")
