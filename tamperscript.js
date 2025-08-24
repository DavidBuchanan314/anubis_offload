// ==UserScript==
// @name         Anubis Offloader
// @namespace    http://tampermonkey.net/
// @version      2024-10-27
// @description  blah
// @author       You
// @match        *://*/*
// @grant        none
// @run-at document-start
// ==/UserScript==

(function() {
    'use strict';

const OFFLOAD_URL = "http://localhost:1237/anubis_offload"

function hook_proto(clazz, method_name, hook_impl) {
	const orig_impl = clazz.prototype[method_name];

	// can't use arrow syntax because we need "this"
	clazz.prototype[method_name] = function() {
		return hook_impl(this, orig_impl.bind(this), arguments);
	}

	// TODO: try to hide the hook from anyone doing introspection
}

const ANUBIS_KEYS = new Set(["data", "difficulty", "nonce", "threads"]);
function looks_like_anubis_pow(message) {
	if (typeof message !== "object") return false;
	if (!Object.keys(message).every(k => ANUBIS_KEYS.has(k))) return false;
	if (typeof message.data !== "string") return false;
	if (typeof message.difficulty !== "number") return false;
	if (typeof message.nonce !== "number") return false;
	if (typeof message.threads !== "number") return false;
	return true;
}

hook_proto(window.Worker, "postMessage", (that, orig, [message, options]) => {
	console.log("hooked postMessage", message, options);
	
	// passthru for non-anubis-y messages
	if (!looks_like_anubis_pow(message)) {
		return orig(message, options);
	}

	if (message.nonce == 0) { // first thread
		console.log("detected anubis PoW message:", message);
		fetch(OFFLOAD_URL, {
			method: "POST",
			body: JSON.stringify(message)
		}).then(res => res.json()).then(res => {
			console.log("received PoW result:", res);
			that.onmessage({data: res})
		});
	}
});


})();
