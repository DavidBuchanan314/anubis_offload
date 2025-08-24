from aiohttp import web
import time

from cpumine import cpumine
from oclmine import OCLMiner

routes = web.RouteTableDef()

@routes.get("/")
async def hello(request: web.Request):
	return web.Response(text="Hello, offloadd")

@routes.post("/anubis_offload")
async def offload(request: web.Request):
	message = await request.json()
	print("request", message)
	data, difficulty = message["data"], message["difficulty"]
	start = time.time()
	if 0:
		found_nonce, found_hash = await cpumine(data, difficulty)
	else:
		found_nonce, found_hash = request.app["miner"].mine(data, difficulty)
	duration = time.time() - start
	print(f"found {found_nonce} in {int(duration*1000)}ms")
	return web.json_response(
		{
			"hash": found_hash,
			"data": data,
			"difficulty": difficulty,
			"nonce": str(found_nonce) # make sure it survives jsonification!
		},
		headers={
			"Access-Control-Allow-Origin": "*"
		}
	)


if __name__ == "__main__":
	app = web.Application()
	app["miner"] = OCLMiner()
	app.add_routes(routes)
	web.run_app(app, port=1237)
