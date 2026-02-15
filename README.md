# mumble-chatdb
Proof of concept Python script to retain a log of chat messages on a mumble-server. I am aware this install is not very user-friendly - try at your own risk!
## Dependencies
Note: Only tested on Debian 12.13. The code contains specific path references for ZeroC Ice. If you want to run this on a different distro, feel free to add an issue or submit a PR.

Required Dependencies (only tested with system-wide installation via sudo apt install):

- python3-zeroc-ice
- zeroc-ice-slice
- python3-sqlalchemy
- zeroc-ice-all-dev

Assumes the mumble server is running on the local system. If not, you can modify the IP in the ICE_HOST string of the mumble_history_bot.py script.

## Installation Notes
If you haven't already, activate the ZeroC Ice protocol on your mumble server by uncommenting the following lines (in your mumble-server.ini):
``` shell
ice="tcp -h 127.0.0.1 -p 6502"
icesecretread=YourSuperDuperSecretPassGoesHere
icesecretwrite=YourSuperDuperSecretPassGoesHere
```
Use whatever your want for the password but I'd recommend something pretty long and random for your server's security, like a SHA256 hash of a random file and timestamp.

I also recommend saving your Ice secret into an environment file (default I chose is /etc/mumble-history-bot.env). In any case the script expects to load that secret from the environment variable "MUMBLE_ICE_SECRET" so however you want to do it, you do you. This is what my file looks like:
``` bash
# /etc/mumble-history-bot.env
MUMBLE_ICE_SECRET=YourSuperDuperSecretPassGoesHere
```

Create the following path:
``` bash
sudo mkdir /opt/mumble-history-bot/
```

Copy the script into that path. You can test the script by running
``` bash
python3 /opt/mumble-history-bot/mumble_history_bot.py
```
Which should work if all dependencies are satisfied.

I recommend creating a system user and service for the script so that it boots up alongside the Mumble server. Delegating this to a system user prevents you from needing to give root permissions.
``` bash
sudo adduser --system --group --no-create-home --home /opt/mumble-history-bot mumblebot
sudo chown -R mumblebot:mumblebot /opt/mumble-history-bot
sudo chmod 755 /opt/mumble-history-bot
sudo chown mumblebot:mumblebot /etc/mumble-history-bot.env
sudo chmod 600 /etc/mumble-history-bot.env
```
Finally, copy the example "mumble-history-bot.service" file here:
``` bash
/etc/systemd/system/mumble-history-bot.service
```
And start the service like so:
``` bash
sudo systemctl daemon-reload
sudo systemctl restart mumble-history-bot
```
## Known Issues

- Uses a single connection to the database and "check_same_thread=False". If you have a very busy server with a lot of messages, data might not be written to the database.
- Stores image data in the original HTML string representation Mumble uses for transmission, which is uncompressed. A lot of images could blow up the database size.
  - That said, I've had it running for about a month on a server with 10-30 users and it is only around 100 MB so far.
- Currently only reacts to "userConnected" events, so you'll get a history log when you first connect to the server, but not when you switch between channels
  - This was a compromise because I found it annoying to constantly get blasted with the channel history every time I switched channels, but probably could implement some kind of per-user logging to tell if they've seen things "recently"
