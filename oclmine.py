import os
import pyopencl as cl
import numpy as np
from sha256 import sha256_prefix

WORK_SIZE = 0x1000
STEPS_PER_TASK = 0x100 # keep in sync with cl source

class OCLMiner():
	def __init__(self) -> None:
		self.initial_h = np.array([
			0x6a09e667,  # h0
			0xbb67ae85,  # h1
			0x3c6ef372,  # h2
			0xa54ff53a,  # h3
			0x510e527f,  # h4
			0x9b05688c,  # h5
			0x1f83d9ab,  # h6
			0x5be0cd19   # h7
		], dtype=np.uint32)
		self.res_flag = np.array([0], dtype=np.uint32)
		self.res_nonce = np.array([0], dtype=np.uint64)

		ctx = cl.create_some_context()

		self.queue = cl.CommandQueue(ctx)

		self.initial_h_buf = cl.Buffer(ctx, cl.mem_flags.READ_WRITE, size=self.initial_h.nbytes)
		self.res_flag_buf = cl.Buffer(ctx, cl.mem_flags.READ_WRITE, size=self.res_flag.nbytes)
		self.res_nonce_buf = cl.Buffer(ctx, cl.mem_flags.READ_WRITE, size=self.res_nonce.nbytes)
		self.res_h_buf = cl.Buffer(ctx, cl.mem_flags.READ_WRITE, size=self.initial_h.nbytes)

		#cl.enqueue_copy(self.queue, self.initial_h_buf, self.initial_h)
		cl.enqueue_copy(self.queue, self.res_flag_buf, self.res_flag)
		cl.enqueue_copy(self.queue, self.res_nonce_buf, self.res_nonce)
		cl.enqueue_copy(self.queue, self.res_h_buf, self.initial_h)

		srcdir = os.path.dirname(os.path.realpath(__file__))
		prg = cl.Program(ctx, open(srcdir + "/sha256.cl").read()).build()
		self.kernel = cl.Kernel(prg, "mine")

	def mine(self, data: str) -> tuple[int, str]:
		print(data)

		initial_h = np.array(sha256_prefix(data.encode()), dtype=np.uint32)
		cl.enqueue_copy(self.queue, self.initial_h_buf, initial_h)

		base = 0
		while True:
			print("working...", hex(base))
			self.kernel(self.queue, (WORK_SIZE,), None, self.res_flag_buf, self.res_nonce_buf, self.res_h_buf, self.initial_h_buf, np.uint64(base), np.uint32(len(data)))
			cl.enqueue_copy(self.queue, self.res_flag, self.res_flag_buf)
			if self.res_flag[0]:
				break
			base += WORK_SIZE * STEPS_PER_TASK

		result = np.empty_like(self.initial_h)
		cl.enqueue_copy(self.queue, result, self.res_h_buf)
		cl.enqueue_copy(self.queue, self.res_nonce, self.res_nonce_buf)

		octalized = int(f"1{int(self.res_nonce[0]):0>18o}")
		hash_out = b"".join(int(x).to_bytes(4, "big") for x in result).hex()
		return octalized, hash_out


if __name__ == "__main__":
	import time
	miner = OCLMiner()
	start = time.time()
	print(miner.mine("A"*64))
	print(time.time()-start)
