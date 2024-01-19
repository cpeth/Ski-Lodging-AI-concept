# Cloud Platform

List of current infrastructure (To be OpenTofu'd/Pulumi'd)


## Persistence

### Cloud Firestore

Main operational DB and ata landing zone

### BigQuery

Data is [replicated](https://extensions.dev/extensions/firebase/firestore-bigquery-export) from Firestore to BigQuery for ease of querying and to power analysis tools.

## Cloud Tasks

Queueing system to control throughput to 3rd party APIs like OpenAI

- openai-review: listing awaiting having reviews evaluated by openai (gpt3.5-turbo-1106). Limited to 1/sec

## Cloud Functions

- apify webhook endpoint: Called when Apify finishes a scrape. Currently just AirBnb
- firestore events: When a new listing is saved to the firestore database, add a Cloud Task item to send it to a LLM for evaluation and embeddings
- open_ai_client: read off the task run queue and send to OpenAI

