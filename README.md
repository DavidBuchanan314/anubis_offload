# anubis_offload
userscript to offload Anubis PoW to native CPU or GPU code. My implementation is pretty janky, but it works.

difficulty 4 (the default) takes tens of milliseconds on CPU, compared to multiple seconds without the userscript.

difficulty 6 (256x harder than difficulty 4) takes tens of milliseconds on GPU (tested on an RX 6700 XT).

I also used an optimized mining algorithm, so that the inner loop only has to re-process the last SHA256 block rather than the whole message (this alone should give a 9x speedup over the naive algorithm).

To use it, install [`tamperscript.user.js`](https://github.com/DavidBuchanan314/anubis_offload/raw/refs/heads/main/tamperscript.user.js) with tampermonkey (or similar userscript tool) and then run `python3 offloadd.py`. Anubis checks in your browser should be virtually instantaneous now.

## Demo Video

First load is with the userscript disabled, second is enabled (with cookies cleared in between)

https://github.com/user-attachments/assets/7202f863-e068-4abc-9944-643511ffd3ed

## How?

Normally, Anubis [computes PoW](https://github.com/TecharoHQ/anubis/blob/main/docs/docs/design/why-proof-of-work.mdx#how-anubis-proof-of-work-scheme-works) in your browser, using multiple worker threads via the [Web Workers API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API/Using_web_workers).

I wrote a tampermonkey script to hook the `Worker.postMessage` API to detect messages that look like Anubis PoW challenges and block them (so no PoW happens in your browser anymore). Then it submits the challenge to a local HTTP server, waits for the result, and fires the `Worker.onmessage` callback just like the original Worker code would've done.

`offloadd.py` implements the HTTP server that handles the PoW challenges, accelerated with pyopencl (there's also a pure-cpu codepath, disabled because opencl is faster, but it's simpler if you just want to see how it works)

## Why?

I don't like watching a slow progress bar computing SHA-256 in javascript at mere KH/s, knowing that my CPU is capable of MH/s, and that I have a fast GPU on my LAN capable of GH/s. This is particularly relevant if you browse from a low-end device.

It also saves the environment a little, I guess.

## Doesn't this undermine the security of Anubis?

It shouldn't do. The idea behind Anubis seems to be that mass scrapers can't be bothered to bypass it, not that they can't. But also, this tool *doesn't* bypass it - we compute the PoW legitimately!

## Why not just change your user-agent to one that Anubis allows unconditionally?

You can do that, if you want - and there are browser extensions that do it: https://addons.mozilla.org/en-GB/firefox/addon/nopow/

~~Personally I don't want to change my UA for all websites (because it breaks things), and curating a manual list of exceptions sounds even more tedious than waiting for PoW to complete.~~

Actually, I believe the above extension figures out which pages need a spoofed UA automatically, maybe it's not so bad after all. UA spoofing seems like something more likely to be used by scrapers though, and therefore more likely to get patched out.

## What About CSP?

Yeah, that's a problem. If a site has a strict CSP configured, our userscript will not be able to reach out to the PoW server. Writing a proper browser extension (as opposed to a userscript) should solve this, but packaging browser extensions is a pain.

I haven't tested on many sites, but all the ones I tried thus far worked fine.

## What if a malicious site sends fake PoW requests, to annoy me?

Sure, they could do that, I guess. But malicious sites can compute PoW in your browser anyway. I've set a difficulty cap in `offloadd` so it shouldn't waste more than 1 minute or so of compute.

## Misc Implementaion Details

Anubis expects the `nonce` value (the thing you search for during mining) to be an integer, which is stringified to decimal before hashing. To simplify the integer-to-string conversion in the inner loop, I use octal rather than decimal, because it's just a matter of branchless bit-twiddling rather than involving division/modulo, or digitwise-long-addition-with-carry. I add `100000...` to the number to keep it a fixed width, and store it in the JSON as a string literal so that the browser doesn't mangle it when it exceeds the 2^53 limit.

My desktop has a beefy-ish GPU, while my laptop(s) do not. I use `ssh -N -L 1237:localhost:1237 my_desktop_addr` to forward the `offloadd` service port - it's important that the browser accesses it via `localhost` because there are security exceptions for HTTP on localhost (otherwise you might get mixed-content exceptions). This is another thing that a proper browser extension might be able to work around.

## Future Improvements

- Just use JS for very-easy challenges below some threshold - the overhead of sending work to the GPU isn't worth it.

- Fall back to JS if the `offloadd` server is offline.

- Use WebGPU. It's not available on my platform right now, though.
