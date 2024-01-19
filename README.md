# SkiGeist

This is an exploratory project for a startup idea centered on improving the way one can plan ski vacations and find great ski-centric properties to stay at. Code quality reflects the prototype/poc nature of this project.

This project is open source soley for building out my github profile and is not intended as a useful tool for others beyond being an example of use of serverless technologies on [GCP](https://cloud.google.com/), Python, LLMs, etc.

## General Idea

Can we create a website that is the best place to plan a ski-vacation?  As a starting goal can we identify the very best places to stay in great ski locations?

### Process

1. Scrape properties. Sadly most property listing aggregators are not accessible via official APIs. Thankfully scraping is perfectly [legal](https://en.wikipedia.org/wiki/HiQ_Labs_v._LinkedIn). For now we will use a prebuilt scraper on [Apify](https://apify.com/dtrungtin/airbnb-scraper).

1. Pull in additional data. What makes a great ski property that is not directly available in a property listing?
    - Proximity to restaurants, bars, spas, rental shops, etc
    - endorsements and reviews from outside sources. trip-advisor, social media

1. Feed language features to LLMs to extract relevant information eg. positive mention of skiing in reviews

1. Get embeddings for positive mentions

1. Potentially train NN or build boosted-tree model

1. Provide fast search for great ski properties using vector search on embeddings
 
