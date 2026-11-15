// offline cache for the Sicily trip page
var V='sicily-v4',CORE=['/italy-2027/','/italy-2027/sicily-booklet.pdf','/gate.js','/italy-2027/manifest.webmanifest','/italy-2027/icons/icon-192.png'];
self.addEventListener('install',function(e){self.skipWaiting();e.waitUntil(caches.open(V).then(function(c){return c.addAll(CORE)}))});
self.addEventListener('activate',function(e){e.waitUntil(caches.keys().then(function(k){return Promise.all(k.filter(function(x){return x!==V}).map(function(x){return caches.delete(x)}))}).then(function(){return self.clients.claim()}))});
self.addEventListener('message',function(e){var urls=(e.data&&e.data.cache)||[],ok=0;caches.open(V).then(function(c){return Promise.all(urls.map(function(u){var same=new URL(u,self.location).origin===self.location.origin;return fetch(u,same?{}:{mode:'no-cors'}).then(function(r){if(r.ok||r.type==='opaque'){ok++;return c.put(u,r)}}).catch(function(){})}))}).then(function(){if(e.ports[0])e.ports[0].postMessage({ok:ok,all:urls.length})})});
self.addEventListener('fetch',function(e){var r=e.request;if(r.method!=='GET')return;var u=new URL(r.url);
 if(u.hostname==='api.open-meteo.com')return;
 if(r.mode==='navigate'||u.pathname==='/gate.js'){e.respondWith(fetch(r).then(function(res){var cp=res.clone();caches.open(V).then(function(c){c.put(r.mode==='navigate'?'/italy-2027/':r,cp)});return res}).catch(function(){return caches.match(r.mode==='navigate'?'/italy-2027/':r)}));return}
 e.respondWith(caches.match(r).then(function(hit){var net=fetch(r).then(function(res){if(res.ok||res.type==='opaque'){var cp=res.clone();caches.open(V).then(function(c){c.put(r,cp)})}return res}).catch(function(){return hit});return hit||net}));
});
