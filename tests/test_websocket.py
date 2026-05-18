import asyncio
import websockets


async def test_websocket():
    uri = "ws://localhost:8000/ws/stream"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            # receive initial connection confirmation
            response = await websocket.recv()
            print(f"Connected: {response}")

            # try to receive a few data messages
            for i in range(3):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout = 35)
                    print(f"Received: {message}")
                except asyncio.TimeoutError:
                    print("Timeout: no data received in 35 seconds")
                    break
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(test_websocket())
