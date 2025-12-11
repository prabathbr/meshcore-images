import asyncio
import os
import base64
from datetime import datetime

from meshcore import MeshCore, EventType
from codec import string_to_image_file

SERIAL_PORT = "COM4"
CHANNEL_IDX = 4

IMAGE_WIDTH = 32
IMAGE_HEIGHT = 18
GAP_SIZE = 4

RX_FOLDER = "rx_frames"


async def main():
    os.makedirs(RX_FOLDER, exist_ok=True)

    meshcore = await MeshCore.create_serial(SERIAL_PORT, debug=True)
    print(f"Connected on {SERIAL_PORT}")

    await meshcore.start_auto_message_fetching()

    rx_counter = {"n": 0}

    async def handle_channel_message(event):
        payload = event.payload

        chan = payload.get("channel_idx")
        text = payload.get("text", "")
        path_len = payload.get("path_len")

        if chan != CHANNEL_IDX:
            return

        print(f"Received on channel {chan}: len(text)={len(text)} | path_len={path_len}")

        # Extract sender + Base64 payload
        raw_text = text
        if ":" in raw_text:
            sender, msg_text = raw_text.split(":", 1)
            sender = sender.strip()
            msg_text = msg_text.strip()
        else:
            sender = "unknown"
            msg_text = raw_text.strip()

        rx_txt = msg_text
        print(f"Received from {sender}, payload length={len(rx_txt)}")

        # Build filename using sender ID
        rx_counter["n"] += 1
        count = rx_counter["n"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        safe_sender = "".join(c for c in sender if c.isalnum() or c in "-_")
        if not safe_sender:
            safe_sender = "unknown"

        output_image_rx = os.path.join(
            RX_FOLDER,
            f"{safe_sender}_{count}_{timestamp}.png"
        )

        print(f"Decoding image into '{output_image_rx}'")

        try:
            rx_bytes = base64.b64decode(rx_txt)
            rx_string = rx_bytes.decode("latin1")

            string_to_image_file(
                rx_string,
                output_image_rx,
                width=IMAGE_WIDTH,
                height=IMAGE_HEIGHT,
                gap=GAP_SIZE,
            )

            print(f"Saved: {output_image_rx}")
            print("Interleaved preview PNG saved as well")

        except Exception as e:
            print(f"Error decoding received image string: {e}")

    # Subscribe before listening
    subscription = meshcore.subscribe(
        EventType.CHANNEL_MSG_RECV,
        handle_channel_message,
        attribute_filters={"channel_idx": CHANNEL_IDX},
    )

    try:
        print(f"Listening for image data on channel {CHANNEL_IDX}...")
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("Stopping listener...")
    finally:
        meshcore.unsubscribe(subscription)
        await meshcore.stop_auto_message_fetching()
        await meshcore.disconnect()
        print("Disconnected")


if __name__ == "__main__":
    asyncio.run(main())
