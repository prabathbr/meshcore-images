import asyncio
import os
import base64
from meshcore import MeshCore, EventType

from codec import image_file_to_transmit_string

SERIAL_PORT = "COM4"   # change this to your serial port
CHANNEL_IDX = 4        # change this to your channel index

IMAGE_WIDTH = 32
IMAGE_HEIGHT = 18


async def main():
    # Connect to MeshCore companion over serial
    meshcore = await MeshCore.create_serial(SERIAL_PORT, debug=True)
    print(f"Connected on {SERIAL_PORT}")

    # Start automatic message fetching from the device (good practice)
    await meshcore.start_auto_message_fetching()

    # Ask user what file to send
    input_filename = input("Enter image filename to send: ").strip()
    if not os.path.isfile(input_filename):
        print(f"File not found: {input_filename}")
        await meshcore.stop_auto_message_fetching()
        await meshcore.disconnect()
        return

    print(f"Encoding '{input_filename}' for transmission")

    # Encode image into internal transmission string (1 char per byte)
    tx_str = image_file_to_transmit_string(
        input_filename,
        width=IMAGE_WIDTH,
        height=IMAGE_HEIGHT,
        threshold=128,
    )

    print(f"Raw transmission string length: {len(tx_str)} characters")

    # Convert to bytes for Base64
    tx_bytes = tx_str.encode("latin1")  # preserves 0–255 exactly

    # Base64 encode for safe transmission over MeshCore text channel
    tx_b64 = base64.b64encode(tx_bytes).decode("ascii")

    print(f"Base64 encoded length: {len(tx_b64)} characters")

    try:
        print(f"Sending encoded image on channel {CHANNEL_IDX}")
        result = await meshcore.commands.send_chan_msg(CHANNEL_IDX, tx_b64)

        if result.type == EventType.ERROR:
            print(f"Error sending encoded image: {result.payload}")
        else:
            print("Encoded image string sent")

    finally:
        await meshcore.stop_auto_message_fetching()
        await meshcore.disconnect()
        print("Disconnected")


if __name__ == "__main__":
    asyncio.run(main())
