# bot.py

import os
import requests
import discord  # type: ignore

API_URL = "https://general-runtime.voiceflow.com/state"


class MyClient(discord.Client):
    def __init__(self, version_id):
        super().__init__()
        self.api_endpoint = f"{API_URL}/{version_id}"
        self.requests_headers = {"Authorization": os.environ["VF_API_KEY"]}

    def interact(self, user_id, request):
        res = requests.post(
            f"{self.api_endpoint}/user/{user_id}/interact",
            json={"request": request},
            headers=self.requests_headers,
        )

        return res

    async def on_ready(self):
        # Print out information when the bot wakes up
        print("Logged in as")
        print(self.user.name)
        print(self.user.id)
        print("------")
        # Send a request to the model without caring about the response
        # Just so that the model wakes up and starts loading
        # self.query({"inputs": {"text": "Hello!"}})
        # ^^ IDK if I want/need this for VF ^^

    async def on_message(self, message):
        """
        Called whenever the bot sees a message in a channel
        """
        # Ignore message if comes from the bot itself
        if message.author.id == self.user.id:
            return

        # Get user id for interact call
        user_id = message.author.username

        # Form interact payload with the content of the message
        request = {"type": "text", "payload": message.content}

        # While the bot is waiting on a response from VF
        # set its status as typing for user-friendliness
        async with message.channel.typing():
            res = self.interact(user_id=user_id, request=request)
            for trace in res.json():
                if trace["type"] == "speak" or trace["type"] == "text":
                    bot_response = trace["payload"]["message"]
                elif trace["type"] == "end":
                    # An end trace means the VF dialog has ended
                    pass

        # This error handling probably won't work for VF
        if not bot_response:
            if "error" in res:
                bot_response = "`Error: {}`".format(res["error"])
            else:
                bot_response = "Hmm... something is not right."

        # Send the model's response to the Discord channel
        await message.channel.send(bot_response)


def main():

    client = MyClient()
    client.run(os.environ["DISCORD_TOKEN"])


if __name__ == "__main__":
    main()
