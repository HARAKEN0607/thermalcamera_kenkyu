import numpy as np
import struct
import time
import ioctl_numbers
from fcntl import ioctl
import cv2

ROWS = 60
COLS = 80
SPI_IOC_MAGIC = ord("k")
start = time.time() # NowTime in PC
VOSPI_FRAME_SIZE = COLS + 2

__handle = open("/dev/spidev0.0", "wb+", buffering=0) # binary writing
__xmit_struct = struct.Struct("=QQIIHBBI") # struct original
__msg_size = __xmit_struct.size # 8+8+4+4+2+1+1+4=32
__xmit_buf = np.zeros((__msg_size * ROWS), dtype=np.uint8) # 32*60 [0 codes]
__capture_buf = np.zeros((ROWS, VOSPI_FRAME_SIZE, 1), dtype=np.uint16) # [60行　82列]の枠に0が一つずつ

def capture(data_buffer=None, log_time=False, debug_print=False, retry_reset=True):

    if data_buffer is None:
        data_buffer = np.ndarray((ROWS, COLS, 1), dtype=np.uint16) # 60行80列に1枠ずつ

    elif data_buffer.ndim < 2 or data_buffer.shape[0] < ROWS or data_buffer.shape[1] < COLS or data_buffer.itemsize < 2:
        raise Exception("Provided input array not large enough")

    while True:
        messages = ROWS
        iow = ioctl_numbers._IOW(SPI_IOC_MAGIC, 0, __msg_size)  # writing mode

        ioctl(__handle, iow, __xmit_buf, True)  # writing to camera

        __capture_buf = np.zeros((ROWS, VOSPI_FRAME_SIZE, 1), dtype=np.uint16)  # [60行　82列]の枠に0が一つずつ

        # __capture_buf[0]=0*82    __capture_buf[0][0]=0    0x000f=[0*14 1]
        # __capture_buf[0][0] & 0x000f = 0

        while (__capture_buf[0][0] & 0x000f) == 0x000f:  # __capture_buf[0]=0*82    __capture_buf[0][0]=0    0x000f=[0*14 1]
            ioctl(__handle, iow, __xmit_buf, True)  # __capture_buf[0][0] & 0x000f = 0

        messages -= 1  # messages(60)-1

        if retry_reset and (__capture_buf[20, 0] & 0xFF0F)!= 0x1400:
            if debug_print:
                print("Garbage frame number reset waiting...")
            time.sleep(0.185)
        else:
            break

    __capture_buf.byteswap(True)
    data_buffer[:,:] = __capture_buf[:,2:]

    end = time.time()

    if debug_print:
      print("---")
      for i in range(ROWS):
        fid = __capture_buf[i, 0, 0]
        crc = __capture_buf[i, 1, 0]
        fnum = fid & 0xFFF
        print("0x{0:04x} 0x{1:04x} : Row {2:2} : crc={1}".format(fid, crc, fnum))
      print("---")

    if log_time:
      print("frame processed int {0}s, {1}hz".format(end-start, 1.0/(end-start)))

    return data_buffer, data_buffer.sum()

a = capture()

cv2.normalize(a, a, 0, 65535, cv2.NORM_MINMAX) # extend contrast
np.right_shift(a, 8, a) # fit data into 8 bits
cv2.imwrite("output.jpg", np.uint8(a)) # write it!


