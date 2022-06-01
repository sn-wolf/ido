# bot.py

import os
import requests
import discord  # type: ignore

API_URL = "https://general-runtime.voiceflow.com/state"
VF_VERSION_ID = "6238e915145eb8f3f4f77b01"

class MyClient(discord.Client):
    def __init__(self, version_id):
        super().__init__()
        self.api_endpoint = f"{API_URL}/{version_id}"
        self.requests_headers = {"Authorization": os.environ["VF_API_KEY"]}

    def interact(self, session_id, request):
        # Dialog manager POST request
        res = requests.post(
            f"{self.api_endpoint}/user/{session_id}/interact",
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

    async def on_group_join(self, channel, user):
        """
        Called when bot is added to a private channel.
        """
        if user.id == self.user.id:
            # Send a request to the bot to wake it up
            self.interact(session_id=channel.id, request={"type": "launch"})

    async def on_message(self, message):
        """
        Called whenever the bot sees a message in a channel
        """
        # Ignore message if comes from the bot itself
        # or from channels the bot isn't in
        if message.author.id == self.user.id or self.user in message.recipients:
            return

        # Get session id for interact call
        session_id = message.channel.id

        # Form interact payload with the content of the message
        request = {"type": "text", "payload": message.content}

        # While the bot is waiting on a response from VF
        # set its status as typing for user-friendliness
        async with message.channel.typing():
            res = self.interact(session_id=session_id, request=request)
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

    client = MyClient(version_id=VF_VERSION_ID)
    client.run(os.environ["DISCORD_TOKEN"])


if __name__ == "__main__":
    main()
