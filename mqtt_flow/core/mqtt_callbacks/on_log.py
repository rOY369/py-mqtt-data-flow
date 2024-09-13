def on_log(client, userdata, level, buf):
    print(f"client {client._client_id} on_log: {buf}")
