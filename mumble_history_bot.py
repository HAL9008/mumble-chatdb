import Ice
Ice.loadSlice('-I/usr/share/ice/slice -I/usr/share/slice /usr/share/slice/Murmur.ice')
import Murmur
import sqlite3
import time
import os

ICE_HOST = "127.0.0.1"
ICE_PORT = 6502
ICE_SECRET = os.environ.get("MUMBLE_ICE_SECRET")
if not ICE_SECRET:
    raise RuntimeError("MUMBLE_ICE_SECRET environment variable not set")
HISTORY_LIMIT = 20

# --- Database Setup ---
conn = sqlite3.connect("/opt/mumble-history-bot/mumble_history.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS messages (
    channel_id INTEGER,
    user TEXT,
    message TEXT,
    timestamp INTEGER
)
""")
conn.commit()

# --- Ice Setup ---
init_data = Ice.InitializationData()
init_data.properties = Ice.createProperties()
init_data.properties.setProperty("Ice.Default.Router", "")
init_data.properties.setProperty(
    "CallbackAdapter.Endpoints",
    "tcp -h 127.0.0.1"
)
init_data.properties.setProperty("Ice.ImplicitContext", "Shared")

communicator = Ice.initialize(init_data)
communicator.getImplicitContext().put('secret', f"{ICE_SECRET}")
proxy = communicator.stringToProxy(
        f"Meta:tcp -h {ICE_HOST} -p {ICE_PORT}"
)
meta = Murmur.MetaPrx.checkedCast(proxy)

servers = meta.getAllServers()
server = servers[0]



class Callback(Murmur.ServerCallback):

    def userConnected(self, state, current=None):
        if state.channel is not None:
            user = server.getState(state.session)
            channel_id = state.channel

            cur.execute("""
                SELECT user, message FROM messages
                WHERE channel_id=?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (channel_id, HISTORY_LIMIT))

            rows = cur.fetchall()[::-1]

            if rows:
                history = "<br />".join(
                    f"<b>[{u}]</b> {m}" for u, m in rows
                )
                server.sendMessage(
                    state.session,
                    f"<b>--- Last {HISTORY_LIMIT} Messages ---</b><br />{history}"
                )

    def userTextMessage(self, user, msg, current=None):
        if msg.channels:
            channel_id = msg.channels[0]

            cur.execute("""
                INSERT INTO messages VALUES (?, ?, ?, ?)
            """, (
                channel_id,
                user.name,
                msg.text,
                int(time.time())
            ))
            conn.commit()

adapter = communicator.createObjectAdapter("CallbackAdapter")
callback = Callback()
proxy = adapter.add(callback, communicator.stringToIdentity("callback"))
callback_proxy = Murmur.ServerCallbackPrx.checkedCast(proxy)
if not callback_proxy:
    print("Failed to cast callback proxy!")
    exit(1)
adapter.activate()
#adapter.addWithUUID(callback)
#adapter.activate()

server.addCallback(callback_proxy)

print("Mumble history bot running...")
communicator.waitForShutdown()
