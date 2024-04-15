#!/bin/bash

# Install the Automated Cleaner

## Setup virtual environment
python3 -m venv venv

if [ -d "venv" ]; then
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "Failed to create virtual environment"
    exit 1
fi

## dependencies
pip install -r requirements.txt

## Ask for openai key
echo "Create an API key at https://platform.openai.com/api-keys"
echo -e "Please enter your OpenAI key:\c"
read OPENAI

echo "OPENAI_API_KEY=$OPENAI" > .env

echo "Installation complete"

