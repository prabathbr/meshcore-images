from PIL import Image
import numpy as np
import os


def load_and_preprocess_image(input_path, size=(60, 33)):
    """Load image, convert to grayscale, resize."""
    img = Image.open(input_path).convert("L")
    img = img.resize(size, Image.LANCZOS)
    return np.array(img, dtype=np.uint8)


def convert_to_1bit(gray_array, threshold=128):
    """Convert grayscale to 1 bit. Pixels >= threshold become 1."""
    return (gray_array >= threshold).astype(np.uint8)


def save_1bit_output_text(bit_array, output_path):
    """Save 1 bit values as CSV text, one row per image row."""
    h, w = bit_array.shape
    with open(output_path, "w") as f:
        for y in range(h):
            f.write(",".join(str(v) for v in bit_array[y]) + "\n")


def save_1bit_png(bit_array, png_path):
    """Save a 1 bit array as a grayscale PNG (0 or 255)."""
    img = Image.fromarray((bit_array * 255).astype(np.uint8), mode="L")
    img.save(png_path)


def pack_8pixels_reversed(group):
    """
    Pack 8 pixels into one byte with reversed bit order.

    Bit 7 <- pixel 7
    Bit 6 <- pixel 6
    ...
    Bit 0 <- pixel 0
    """
    value = 0
    for i in range(8):
        value |= (group[i] & 1) << i
    return value


def save_packed_8pixels_per_byte(bit_array, binary_path):
    """
    Pack 1 bit pixels into bytes, 8 pixels per byte.
    Uses reversed bit order as in pack_8pixels_reversed.
    """
    flat = bit_array.flatten().astype(np.uint8)

    # pad to multiple of 8 pixels
    padding = (-len(flat)) % 8
    if padding:
        flat = np.pad(flat, (0, padding), constant_values=0)

    groups = flat.reshape(-1, 8)
    packed = np.array([pack_8pixels_reversed(g) for g in groups],
                      dtype=np.uint8)

    with open(binary_path, "wb") as f:
        f.write(bytearray(packed.tolist()))


def decode_packed_8pixels_reversed(binary_path, width, height):
    """
    Decode a packed 1 bit file created by save_packed_8pixels_per_byte.

    It assumes:
      bit 7 <- pixel 7
      ...
      bit 0 <- pixel 0

    Returns a 2D numpy array of shape (height, width) with values 0 or 1.
    """
    with open(binary_path, "rb") as f:
        data = f.read()

    bytes_arr = np.frombuffer(data, dtype=np.uint8)

    bits = []
    for byte in bytes_arr:
        for i in range(8):
            bits.append((byte >> i) & 1)

    total_pixels = width * height
    bits = np.array(bits[:total_pixels], dtype=np.uint8)

    return bits.reshape((height, width))


def build_interleaved_image_with_gaps_simple(bit_array, gap=4):
    """
    Build a visualization image with configurable gaps.

    gap controls how many empty rows and columns between pixels.
    This is only for visualization, not for packing.
    """
    h, w = bit_array.shape
    out_h = h + (h - 1) * gap
    out_w = w + (w - 1) * gap

    out = np.zeros((out_h, out_w), dtype=np.uint8)

    for r in range(h):
        for c in range(w):
            out[r * (gap + 1), c * (gap + 1)] = bit_array[r, c]

    return out

def build_interleaved_image_with_gaps(bit_array, gap=4):
    """
    Upscale bit_array to a higher resolution binary image.

    'gap' controls the scale factor via:
        scale = gap + 1

    For example:
        width = 60, height = 33, gap = 4
        scale = 5
        output size = 60 * 5 by 33 * 5

    The output is still 1 bit internally (values 0 or 1)
    so it works correctly with save_1bit_png.
    """
    h, w = bit_array.shape

    scale = gap + 1
    out_w = w * scale
    out_h = h * scale

    # Convert to 0 or 255 for PIL
    base_img = Image.fromarray((bit_array * 255).astype(np.uint8), mode="L")

    # Nearest neighbour keeps pixel colors exact, just larger blocks
    upscaled_img = base_img.resize((out_w, out_h), Image.NEAREST)

    # Convert back to 0 or 1 for the rest of the pipeline
    arr = np.array(upscaled_img, dtype=np.uint8)
    bit_upscaled = (arr >= 128).astype(np.uint8)

    return bit_upscaled




def process_image_to_1bit(input_path,
                          text_out,
                          png_out,
                          bin_out,
                          size=(60, 33),
                          threshold=128):
    """
    Encode pipeline:
      image -> grayscale -> 1 bit -> text, PNG, packed binary.
    """
    gray = load_and_preprocess_image(input_path, size=size)
    bits = convert_to_1bit(gray, threshold)

    save_1bit_output_text(bits, text_out)
    save_1bit_png(bits, png_out)
    save_packed_8pixels_per_byte(bits, bin_out)

    return bits


def decode_packed_and_make_interleaved_png(bin_path,
                                           interleaved_png_path,
                                           width,
                                           height,
                                           gap_size=4):
    """
    Decode output_1bit_packed.bin and generate
    output_1bit_interleaved_gaps.png from it.
    """
    decoded_bits = decode_packed_8pixels_reversed(bin_path,
                                                  width=width,
                                                  height=height)
    inter_img = build_interleaved_image_with_gaps(decoded_bits,
                                                  gap=gap_size)
    save_1bit_png(inter_img, interleaved_png_path)


def main():
    INPUT_IMAGE_PATH = "input_image2.jpg"

    OUTPUT_TEXT = "output_1bit.txt"
    OUTPUT_PNG = "output_1bit.png"
    OUTPUT_BIN = "output_1bit_packed.bin"

    INTERLEAVED_PNG = "output_1bit_interleaved_gaps.png"

    TARGET_WIDTH = 32 #60
    TARGET_HEIGHT = 18 #33
    TARGET_SIZE = (TARGET_WIDTH, TARGET_HEIGHT)
    THRESHOLD = 128
    GAP_SIZE = 4

    # Encode: image -> packed binary (and normal PNG, text)
    process_image_to_1bit(
        INPUT_IMAGE_PATH,
        OUTPUT_TEXT,
        OUTPUT_PNG,
        OUTPUT_BIN,
        size=TARGET_SIZE,
        threshold=THRESHOLD,
    )

    # Decode: packed binary -> interleaved gaps PNG
    decode_packed_and_make_interleaved_png(
        OUTPUT_BIN,
        INTERLEAVED_PNG,
        width=TARGET_WIDTH,
        height=TARGET_HEIGHT,
        gap_size=GAP_SIZE,
    )

    print("Done. Packed bin created and decoded into interleaved gaps PNG.")

def image_file_to_transmit_string(image_path,
                                  width=32,
                                  height=18,
                                  threshold=128):
    """
    Full encode pipeline for transmission.
    Input: image file path
    Output: a transmission string (each char = 1 byte).
    """
    # Step 1 load and resize
    gray = load_and_preprocess_image(image_path, size=(width, height))

    # Step 2 convert to 1bit
    bits = convert_to_1bit(gray, threshold=threshold)

    # Step 3 pack into bytes (same as output_1bit_packed.bin)
    flat = bits.flatten().astype(np.uint8)

    padding = (-len(flat)) % 8
    if padding:
        flat = np.pad(flat, (0, padding), constant_values=0)

    groups = flat.reshape(-1, 8)
    packed_bytes = [pack_8pixels_reversed(g) for g in groups]

    # Step 4 convert bytes → string
    tx_string = ''.join(chr(b) for b in packed_bytes)
    return tx_string


def string_to_image_file(transmit_string,
                         output_png_path,
                         width=32,
                         height=18):
    """
    Full decode pipeline for received data.
    Input: transmission string (each char = 1 byte)
    Output: reconstructed image saved at output_png_path
    """
    # Step 1 string → byte array
    byte_values = [ord(c) for c in transmit_string]

    # Step 2 unpack bytes → 1bit pixels
    bits = []
    for byte in byte_values:
        for i in range(8):
            bits.append((byte >> i) & 1)

    total_pixels = width * height
    bits = np.array(bits[:total_pixels], dtype=np.uint8)
    bit_image = bits.reshape((height, width))

    # Step 3 save final PNG image
    save_1bit_png(bit_image, output_png_path)

    return bit_image


def string_to_image_file(transmit_string,
                         output_png_path,
                         width=32,
                         height=18,
                         gap=8):
    """
    Decode transmission string into:
      1) Base 1bit PNG image
      2) Interleaved visualization PNG with gaps
         File name will be auto-generated:
           output.png -> output_interleaved.png

    Returns:
      The base 1bit image as a numpy array (height x width).
    """
    # --------------------------
    # Step 1 Convert string -> bytes
    # --------------------------
    byte_values = [ord(c) for c in transmit_string]

    # --------------------------
    # Step 2 Unpack bits
    # --------------------------
    bits = []
    for byte in byte_values:
        for i in range(8):
            bits.append((byte >> i) & 1)

    total_pixels = width * height
    bits = np.array(bits[:total_pixels], dtype=np.uint8)
    bit_image = bits.reshape((height, width))

    # --------------------------
    # Step 3 Save main image
    # --------------------------
    save_1bit_png(bit_image, output_png_path)

    # --------------------------
    # Step 4 Automatically build interleaved filename
    # --------------------------
    base, ext = os.path.splitext(output_png_path)
    interleaved_png_path = f"{base}_interleaved{ext}"

    # --------------------------
    # Step 5 Generate interleaved visualization
    # --------------------------
    inter_img = build_interleaved_image_with_gaps(bit_image, gap=gap)
    save_1bit_png(inter_img, interleaved_png_path)

    return bit_image


if __name__ == "__main__":
    main()
    input_filename = "input_image2.jpg"
    tx_str = image_file_to_transmit_string(input_filename)
    print("Transmission")
    rx_string = tx_str
    string_to_image_file(rx_string, "received.png")

