# jamal_bot

Jamal Bot is custom Discord bot with the main goal to hold quotes in a database and be able to access them through Discord. This project's main goals was to familiarize myself with SQL commands and python scripting to build an actual working product. This is honestly quite a mess but it works.

## Instructions

### Requirements

- Python 3.10 (Tested only on 3.10)
- Latest jamal_bot release

### Setup

Inside of the unpacked jamal_bot directory

```sh
# create virtual env
mkdir .venv
python3 -m venv .venv
# activate virtual env
source .venv/bin/activate
# install required packages to the virtual enviroment
python3 -m pip install -r requirements.txt
```

### Configuration

```sh
# copy over default .env and configure
cp .env.example .env
```

### Starting the bot

```sh
# Activate virtual environment if not already activated
source .venv/bin/activate
# Run the bot
python3 jamal_bot_core.py
```

## Help

To access the bot's help message send `jamal help` in a channel the bot can read and write.

## Removing quotes

Currently the bot cannot remove quotes from the database because I don't know how I want to implement this thank you for understanding 👍
