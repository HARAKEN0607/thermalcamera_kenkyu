import numpy as np
import struct
import time
import ioctl_numbers
from fcntl import ioctl

start = time.time()

if data_buffer is None:
    data_buffer = np.ndarray((Lepton.ROWS, Lepton.COLS, 1), dtype=np.uint16)
