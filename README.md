# anubis_offload
userscript to offload Anubis PoW to native CPU or GPU code

difficulty 4 (the default) takes tens of milliseconds on CPU, compared to multiple seconds without the userscript.

I also used an optimized mining algorithm, so that the inner loop only has to re-process the last SHA256 block rather than the whole message.

## How?

Normally, Anubis computes PoW in your browser, using multiple worker threads via the [Web Workers API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API/Using_web_workers).

I wrote a tampermonkey script to hook the `Worker.postMessage` API to detect messages that look like Anubis PoW challenges and block them (so no PoW happens in your browser anymore). Then it submits the challenge to a local HTTP server, waits for the result, and fires the `Worker.onmessage` callback just like the original Worker code would've done.

`offloadd.py` implements the HTTP server that handles the PoW challenges. Yes, the PoW is Python, but it's multithreaded and the SHA-256-ing happens in native code, so it's a lot faster than pure JS.

## Why?

I don't like watching a slow progress bar computing SHA-256 in javascript at mere KH/s, knowing that my CPU is capable of MH/s, and that I have a fast GPU on my LAN capable of GH/s. This is particularly relevant if you browse from a low-end device.

It also saves the environment a little, I guess.

## Doesn't this undermine the security of Anubis?

It shouldn't do. The idea behind Anubis seems to be that mass scrapers can't be bothered to bypass it, not that they can't. But also, we *don't* bypass it - we compute the PoW legitimately!

## Why not just change your user-agent to one that Anubis allows unconditionally?

You can do that, if you want - and there are browser extensions that do it: https://addons.mozilla.org/en-GB/firefox/addon/anubis-bypass/

Personally I don't want to change my UA for all websites (because it breaks things), and curating a manual list of exceptions sounds even more tedious than waiting for PoW to complete.

## What About CSP?

Yeah, that's a problem. If a site has a strict CSP configured, our userscript will not be able to reach out to the PoW server. Writing a proper browser extension (as opposed to a userscript) should solve this, but packaging browser extensions is a pain.

## What if a malicious site sends fake PoW requests, to annoy me?

Sure, they could do that, I guess. But malicious sites can compute PoW in your browser anyway. I've set a cap in `offloadd` so it shouldn't waste more than 1 minute of compute (TODO: actually do this!!!).
