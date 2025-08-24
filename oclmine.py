import os
import pyopencl as cl
import numpy as np

initial_h = np.array([
	0x6a09e667,  # h0
	0xbb67ae85,  # h1
	0x3c6ef372,  # h2
	0xa54ff53a,  # h3
	0x510e527f,  # h4
	0x9b05688c,  # h5
	0x1f83d9ab,  # h6
	0x5be0cd19   # h7
], dtype=np.uint32)
res_flag = np.array([0], dtype=np.uint32)
res_nonce = np.array([0], dtype=np.uint64)

ctx = cl.create_some_context()

queue = cl.CommandQueue(ctx)

initial_h_buf = cl.Buffer(ctx, cl.mem_flags.READ_WRITE, size=initial_h.nbytes)
res_flag_buf = cl.Buffer(ctx, cl.mem_flags.READ_WRITE, size=res_flag.nbytes)
res_nonce_buf = cl.Buffer(ctx, cl.mem_flags.READ_WRITE, size=res_nonce.nbytes)
res_h_buf = cl.Buffer(ctx, cl.mem_flags.READ_WRITE, size=initial_h.nbytes)

cl.enqueue_copy(queue, initial_h_buf, initial_h)
cl.enqueue_copy(queue, res_flag_buf, res_flag)
cl.enqueue_copy(queue, res_nonce_buf, res_nonce)
cl.enqueue_copy(queue, res_h_buf, initial_h)

srcdir = os.path.dirname(os.path.realpath(__file__))
prg = cl.Program(ctx, open(srcdir + "/sha256.cl").read()).build()
kernel = cl.Kernel(prg, "twice")

WORK_SIZE = 0x20
STEPS_PER_TASK = 0x100 # keep in sync with cl source

base = 0
while True:
	print("working...", hex(base))
	kernel(queue, (WORK_SIZE,), None, res_flag_buf, res_nonce_buf, res_h_buf, initial_h_buf, np.int64(base))
	cl.enqueue_copy(queue, res_flag, res_flag_buf)
	if res_flag[0]:
		break
	base += WORK_SIZE * STEPS_PER_TASK

result = np.empty_like(initial_h)
cl.enqueue_copy(queue, result, res_h_buf)
cl.enqueue_copy(queue, res_nonce, res_nonce_buf)

print(int(res_flag[0]))
print(f"1{int(res_nonce[0]):0>18o}")
print(b"".join(int(x).to_bytes(4, "big") for x in result).hex())
