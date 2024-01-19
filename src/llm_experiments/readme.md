# LLM Experiments

This directory contains files and data for experimenting with LLMs. Our goal is to get an LLM to usefully rate short term rental property listings sourced from scrapes of AirBnb / VRBO  ski properties within a certain segment. 

**As this is for quick experiements, it does *NOT* have clean / well-structured code.**

### Dependencies
|Source|Purpose|
|------|-------|
|[Python 3.12](https://www.python.org/downloads/release/python-3120/)||
|[rustup.rs](https://rustup.rs)|Rust is required for tiktoken|
|https://github.com/openai/openai-python|calling ChatGTP API|
|https://github.com/openai/tiktoken|making sure we stay within context-window limits|
|https://pypi.org/project/backoff/|exponential backoff on token-rate limit errors|
|https://github.com/guidance-ai/guidance|easily testing many models with less templated responses|

When I have time I will bake these into the devcontainter. For now:

```sh
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
pip install openai tiktoken guidance backoff
```

## Running

```sh
export OPENAI_API_KEY={Your Open API Key}
cd src/llm_experiments/
python open_ai_wholeistic.py
```

## OpenAI

### Chat API

We will first use the Chat API instead of assistants because of JSON mode and streaming capabilities.

### Assistant API

Currently the Assistant API doeesn't allow for JSON output guarantees like the ChatAPI: https://community.openai.com/t/json-response-format-with-assistant-runs/485449 but it may be worth experimenting with due to it's document fetch capabilities.

## Guidance

Guidance allows us to interact with many models while writing less code to parse responses.