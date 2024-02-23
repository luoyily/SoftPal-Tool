import numpy as np
import argparse

def rol(byte, shift):
    shift %= 8
    binary = bin(byte)[2:].zfill(8)
    binary_shift = binary[shift:]+binary[:shift]
    return int(binary_shift, base=2)


def pal_file_decrypt(byte_array):
    data = byte_array
    shift = 4
    for i in range(16, len(byte_array)-4, 4):
        data[i] = rol(data[i], shift)
        dword = np.frombuffer(data[i:i+4], dtype=np.uint32, count=1)[0]
        dword = dword ^ np.uint32(0x084DF873) ^ np.uint32(0xFF987DEE)
        data[i:i+4] = [int(b) for b in dword.tobytes()]
        shift += 1
    return data

# python run
# data = np.fromfile('Text.dat', dtype=np.uint8)
# d = pal_file_decrypt(data)
# d.tofile('text_dec.dat')

# cli
parser = argparse.ArgumentParser()
parser.add_argument('-f', help='File to be decrypted')

args = parser.parse_args()
data = np.fromfile(args.f, dtype=np.uint8)
decrypted_data = pal_file_decrypt(data)
decrypted_data.tofile(args.f+'.dec')
