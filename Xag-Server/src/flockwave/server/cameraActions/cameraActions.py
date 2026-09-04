import asks

asks.init("trio")

global_urls = [
    "http://192.168.6.151:8000",
    "http://192.168.6.155:8000",
]


async def start():
    global global_urls
    base_url = global_urls
    for url in base_url:
        print(f"{url}/start_capture")
        response = await asks.post(url)
        print(response.json())
    return True


async def stop():
    global global_urls
    base_url = global_urls
    for url in base_url:
        print(f"{url}/stop_capture")
        response = await asks.post(url)
        print(response.json())
    return True
