from hashlib import sha256
import asyncio
from multiprocessing import Queue, Process, cpu_count

def mine_worker(resq: Queue, challenge: str, difficulty=4, start=0, stride=1):

	prefix = sha256()
	prefix.update(challenge.encode())

	leading_bytes = bytes(difficulty//2)
	i = start
	while True:
		tmp = prefix.copy()
		tmp.update(str(i).encode())
		digest = tmp.digest()
		if digest.startswith(leading_bytes):
			hexdigest = digest.hex()
			if hexdigest.startswith("0"*difficulty):
				resq.put((i, hexdigest))
				return
		i += stride

def cpumine_blocking(challenge: str, difficulty=4) -> tuple[int, str]:
	nprocs = cpu_count()
	resq = Queue()
	threads = [Process(
		target=mine_worker,
		args=(resq, challenge, difficulty, i, nprocs)
	) for i in range(nprocs)]
	for thread in threads:
		thread.start()
	res = resq.get()
	for thread in threads:
		thread.kill()
	return res

async def cpumine(challenge: str, difficulty=4) -> tuple[int, str]:
	return await asyncio.get_event_loop().run_in_executor(None, cpumine_blocking, challenge, difficulty)

async def main():
	print(await cpumine("32f07ef7dc9ac2982a403350549942cf4be9922e2aa6c9a0f5cf50ad914f12abc12db5b6de8204a8e6de91b86e4950a2c2105fbcae7244d6ead4acd52d78c1086fc5f7c4658af7d0f95d3bdfb253727e4ae34fc27736fd78f5a434125a12df2088557d5f96b408274fe25b89ac2f30a1c1ff4f3cc8d7d7fb7dc495ba30327de8f198e71b452c17dce66d043d1c3f928079d1242f8b43171d584b7a6e8b6f3fbfeb4d09286167ec615c8b5aa3aee0c97004cf037f2afe5a9cacbd7624b5fba39993ad87b05b8d0c6a695ac88d7217457511a8e3f9ace567c9120c491a77e8f41a2d5431315b998e30c0d6fd42a5f3e3dcbe3f309698410d10d9a702a02e799a23", 6))

if __name__ == "__main__":
	asyncio.run(main())
