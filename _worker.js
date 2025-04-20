export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    // Serve static files from the static directory
    if (url.pathname.startsWith('/static/')) {
      const response = await env.ASSETS.fetch(request);
      if (response.status === 200) {
        return response;
      }
    }

    // Forward all other requests to the Python application
    const pythonResponse = await fetch(`http://127.0.0.1:8000${url.pathname}${url.search}`, {
      method: request.method,
      headers: request.headers,
      body: request.body
    });

    return pythonResponse;
  }
}; 