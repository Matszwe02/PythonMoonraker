# Python wrapper for moonraker API

Eamples:

```py
m = Moonraker('127.0.0.1')
m.api.printer_info()['result']['config_file']
```


```py
api = MoonrakerAPI('127.0.0.1')
api.printer_info()['result']['config_file']
```


```py
ws = MoonrakerWS('127.0.0.1')
def handle_message(data: dict):
    print(data)

def main():
    ws.start_websocket_loop(handle_message)
    try:
        while True:
            pass # Do something
    except KeyboardInterrupt:
        ws.stop_websocket_loop()
```