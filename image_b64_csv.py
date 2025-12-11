import os
import base64
import csv

from codec import image_file_to_transmit_string

# Configure these
IMAGE_FOLDER = "test_images"          # folder containing images
OUTPUT_CSV = "tx_b64_mapping.csv"     # output CSV file
IMAGE_WIDTH = 32
IMAGE_HEIGHT = 18
THRESHOLD = 128


def is_image_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in {".png", ".jpg", ".jpeg", ".bmp", ".gif"}


def main():
    if not os.path.isdir(IMAGE_FOLDER):
        print(f"Folder not found: {IMAGE_FOLDER}")
        return

    files = sorted(f for f in os.listdir(IMAGE_FOLDER) if is_image_file(f))

    if not files:
        print(f"No image files found in folder: {IMAGE_FOLDER}")
        return

    print(f"Found {len(files)} image files in {IMAGE_FOLDER}")
    print(f"Writing CSV to {OUTPUT_CSV}")

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        
        # Correct header line
        writer.writerow(["filename", "tx_b64"])

        for fname in files:
            path = os.path.join(IMAGE_FOLDER, fname)
            print(f"Processing {path}...")

            # Encode image into internal transmission string
            tx_str = image_file_to_transmit_string(
                path,
                width=IMAGE_WIDTH,
                height=IMAGE_HEIGHT,
                threshold=THRESHOLD,
            )

            # Convert to bytes then base64
            tx_bytes = tx_str.encode("latin1")
            tx_b64 = base64.b64encode(tx_bytes).decode("ascii")

            # Write row
            writer.writerow([fname, tx_b64])

    print("Done.")


if __name__ == "__main__":
    main()
