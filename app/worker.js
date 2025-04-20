addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  // Forward the request to your Python application
  const url = new URL(request.url)
  const response = await fetch(`http://127.0.0.1:8000${url.pathname}${url.search}`, {
    method: request.method,
    headers: request.headers,
    body: request.body
  })
  
  return response
} 