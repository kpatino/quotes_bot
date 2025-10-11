# quotes_bot

Quotes Bot is custom Discord bot with the main goal to hold quotes in a database and be able to access them through Discord. This project's main goals was to familiarize myself with SQL commands and python scripting to build an actual working product. This is honestly quite a mess but it works.

## Instructions

### Requirements

- Python 3.14
- Latest quotes_bot release or master

### Setup

Inside of the unpacked quotes_bot directory

```sh
# create virtual env
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
python3 bot.py
```

## Removing quotes

Currently the bot cannot remove quotes from the database because I don't know how I want to implement this thank you for understanding 👍
