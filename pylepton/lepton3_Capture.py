import numpy as np
# import struct
import time
# import ioctl_numbers
# from fcntl import ioctl

ROWS = 60
COLS = 80

start = time.time() # NowTime in PC

data_buffer = np.ndarray((ROWS, COLS, 1), dtype=np.uint16) # 60行80列に1枠ずつ

print(data_buffer)

