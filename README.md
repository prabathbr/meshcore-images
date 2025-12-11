# meshcore-images
A simple library to send and receive small images with MeshCore 

Tested with output images with width=32, height=18, black and white.
Automatically converts any input image.

- codec.py = encoding and decoding functions
- image_rx.py = MeshCore Rx client, automatically saves Rx images
- image_tx.py = Sending images as MeshCore messages
- tx_rx_test.py = Test script with both Tx and Rx
- image_b64_csv.py = Converts a folder with images to Tx strings for testing the Rx client


Sample Tx image source: https://commons.wikimedia.org/wiki/File:Warning_Symbol.png  
Tx code `AAAAAAAAAAAAAAAAAIAAAACAAQAAwAMAAOAHAABwDgAAeB4AAHw+AAB+fgAA//8AgH/+AMD//wHg//8D8P//BwAAAAAAAAAA`  
Sample Rx : Sample_Rx.png
