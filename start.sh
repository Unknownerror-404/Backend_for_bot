#!/usr/bin/env bash

# Train the model
rasa train

# Run the Rasa server
rasa run --enable-api --cors "*" --debug
