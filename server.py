import os
import asyncio
from aiohttp import web


WS_FILE = os.path.join(os.path.dirname(__file__), 'index.html')


def init():
    app = web.Application()
    app["sockets"] = []
    app.router.add_get("/", wshandler)
    app.on_shutdown.append(on_shutdown)


web.run_app(init())


async def wshandler(request: web.Request):
    resp = web.WebSocketResponse()
    available = resp.can_prepare(request)
    if not available:
        with open(WS_FILE, "rb") as fp:
            return web.Response(body=fp.read(), content_type="text/html")

    await resp.prepare(request)

    await resp.send_str("Привет!!!")

    try:
        print("Кто-то присоеденился.")
        for ws in request.app["sockets"]:
            await ws.send_str("Кто-то присоеденился.")
        request.app["sockets"].append(resp)

        async for msg in resp:
            if msg.type == web.WSMsgType.TEXT:
                for ws in request.app["sockets"]:
                    if ws is not resp:
                        await ws.send_str(msg.data)
            else:
                return resp
        return resp

    finally:
        request.app["sockets"].remove(resp)
        print("Кто-то отключился.")
        for ws in request.app["sockets"]:
            await ws.send_str("Кто-то отключился.")


async def on_shutdown(app: web.Application):
    for ws in app["sockets"]:
        await ws.close()


from asyncio import Queue


async def producer(channel):
    for num in range(0, 5):
        await asyncio.sleep(1)
        await channel.put(num)


async def consumer(channel: asyncio.Queue):
    while True:
        item = await channel.get()
        print(f'Got number {item}')


async def main():
    channel = asyncio.Queue()
    cons = asyncio.create_task(consumer(channel))

    await producer(channel)
    print('Готово!')


asyncio.run(main())