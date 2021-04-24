import yaml

default_config = {
    "ADMIN_ROLE_ID" : 19234567890,
    "DISCORD_API_KEY": "DISCORD_API_KEY_HERE",
    "OWNER_ID" : 19234567890
}
user_config = {}

def create_config():
    with open('config.yml', 'w') as f:
        yaml.dump(default_config, f)

try:
    with open('config.yml') as config:
        user_config = yaml.safe_load(config)
except FileNotFoundError:
    print("config.yml does not exist! Creating one with default values.")
    create_config()
    exit()