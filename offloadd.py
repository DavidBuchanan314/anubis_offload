from aiohttp import web
from cpumine import cpumine
import time

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
	found_nonce, found_hash = await cpumine(data, difficulty)
	duration = time.time() - start
	print(f"found {found_nonce} in {int(duration*1000)}ms ({int(found_nonce/duration)}H/s)")
	return web.json_response(
		{
			"hash": found_hash,
			"data": data,
			"difficulty": difficulty,
			"nonce": found_nonce
		},
		headers={
			"Access-Control-Allow-Origin": "*"
		}
	)


if __name__ == "__main__":
	app = web.Application()
	app.add_routes(routes)
	web.run_app(app, port=1237)
