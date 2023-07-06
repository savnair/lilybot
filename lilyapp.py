import os, re
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from pymongo import MongoClient

os.environ["SSL_CERT_FILE"] = "/Users/savitha/PycharmProjects/lilybot/venv/lib/python3.11/site-packages/certifi/cacert.pem"

# SLACK APP INIT
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# CONNECT TO DB
client = MongoClient('mongodb+srv://user1:test123@homedepot.3p0igbw.mongodb.net/?retryWrites=true&w=majority')
db = client['homedepot']
collection = db['depotpdp']


# BOT FUNCTIONALITIES
@app.message(re.compile(r"(?i)hello|hey|hi"))
def message_hello(message, say):
    say(f"Hey there, <@{message['user']}>! Please ask me about a Saatva product using the following question format: What is the [--] of [product name]?")

@app.event("message")
def handle_message(event, say):
    text = event["text"]
    channel = event["channel"]

    key = ' of '
    if key in text.lower():
        after = text.split(key, 1)[-1].strip()
        after_nomark = after.replace("?", "")
        name = after_nomark.strip()

        if "price" in text.lower():
            res = retrieve(name, "price")
            response = "The price of this product is " + res

        elif 'category' in text.lower():
            res = retrieve(name, "category")
            response = "The category of this product is " + res

        elif 'rating' in text.lower():
            res = retrieve(name, "rating")
            response = "The rating of this product is " + res

        elif 'dimensions' in text.lower():
            res = retrieve(name, "dimensions")
            response = "The dimensions of this product are " + res

        elif 'url' in text.lower():
            res = retrieve(name, "url")
            response = "The link to this product is " + res

        else:
            response = "This is not a supported question, sorry!"

        say(response, channel=channel)

    else:
        say("Please use the following question format: What is the [--] of [product name]?")


def retrieve(target_name, target_field):
    res = collection.find_one({"name": target_name})
    target = res[target_field]
    return target


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
