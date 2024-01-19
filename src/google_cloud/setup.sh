# Not intended to be run as a script, but rather to be run line by line in the terminal

gcloud auth activate-service-account --key-file=credentials/ski-geist-poc-bf6d542b73ce.json
export GOOGLE_APPLICATION_CREDENTIALS=/workspaces/SkiGeist/src/google_cloud/credentials/ski-geist-poc-487910aaa5c1.json
gcloud config set project ski-geist-poc
gcloud services enable cloudfunctions.googleapis.com cloudbuild.googleapis.com \
 cloudbuild.googleapis.com \
 artifactregistry.googleapis.com \
 run.googleapis.com \
 logging.googleapis.com \
 firestore.googleapis.com \
 cloudscheduler.googleapis.com \
 pubsub.googleapis.com \
 secretmanager.googleapis.com \
 eventarc.googleapis.com 

# Create firestore database
gcloud firestore databases create --location=us-west2 --database=integrations

# Deploy cloud function
gcloud functions deploy apify_airbnb_success \
--gen2 \
--runtime=python312 \
--region=us-west1 \
--source=./apify/ \
--entry-point=airbnb_success_request_handler \
--trigger-http \
--allow-unauthenticated


# Deploy auth test function
gcloud functions deploy auth_test \
--gen2 \
--runtime=python312 \
--region=us-west1 \
--source=./apify/ \
--entry-point=auth_test_handler \
--trigger-http \
--allow-unauthenticated

gcloud functions deploy handle_firestore_event \
--gen2 \
--runtime=python312 \
--region=us-west1 \
--trigger-location=us-west1 \
--source=./firestore_events/ \
--entry-point=handle_firestore_event \
--trigger-event-filters=type=google.cloud.firestore.document.v1.created \
--trigger-event-filters=database='(default)' \
--trigger-event-filters-path-pattern=document='airbnb/{id}'

gcloud functions deploy openai_review \
--gen2 \
--runtime=python312 \
--region=us-west1 \
--source=./openai/ \
--entry-point=openai_review \
--trigger-http \
--allow-unauthenticated