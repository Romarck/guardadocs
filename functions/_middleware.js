export async function onRequest(context) {
  try {
    // Get the request from the context
    const request = context.request;
    
    // Create URL object
    const url = new URL(request.url);
    
    // Forward the request to your Python application
    const response = await fetch(`http://127.0.0.1:8000${url.pathname}${url.search}`, {
      method: request.method,
      headers: request.headers,
      body: request.body
    });
    
    return response;
  } catch (err) {
    return new Response(`Server Error: ${err.message}`, {
      status: 500,
    });
  }
} 