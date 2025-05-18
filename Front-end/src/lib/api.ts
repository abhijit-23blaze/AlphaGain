import axios from 'axios';
import type { Message } from './types';

const API_URL = 'http://localhost:8000';

export async function fetchChatResponse(messages: Message[]) {
  try {
    // Use the non-streaming endpoint
    const response = await axios.post(`${API_URL}/api/chat/json`, { messages });
    return response.data;
  } catch (error) {
    console.error('Error calling chat API:', error);
    throw error;
  }
}

export function streamChatResponse(
  messages: Message[], 
  onChunk: (chunk: string) => void,
  onDone: () => void,
  onError: (error: Error) => void,
  signal?: AbortSignal
) {
  // Use the fetch API with a more robust approach for streaming
  fetch(`${API_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages }),
    signal // Pass the AbortSignal to allow stopping the request
  })
  .then(response => {
    if (!response.body) {
      throw new Error('ReadableStream not supported');
    }

    // Get a reader from the response body stream
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    // Read the stream
    function readStream() {
      // Check if the request was aborted before reading
      if (signal?.aborted) {
        reader.cancel().catch(e => console.error('Error cancelling reader:', e));
        onError(new DOMException('Request aborted', 'AbortError'));
        return;
      }

      reader.read().then(({ done, value }) => {
        // Check if the request was aborted after reading
        if (signal?.aborted) {
          reader.cancel().catch(e => console.error('Error cancelling reader:', e));
          onError(new DOMException('Request aborted', 'AbortError'));
          return;
        }

        if (done) {
          onDone();
          return;
        }

        // Decode the received chunk
        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;

        // Process complete SSE events in buffer
        const events = buffer.split('\n\n');
        buffer = events.pop() || ''; // Keep any incomplete event in the buffer

        for (const event of events) {
          if (!event.trim() || !event.startsWith('data: ')) continue;
          
          const data = event.substring(6); // Remove 'data: ' prefix
          
          if (data === '[DONE]') {
            onDone();
            return;
          }
          
          try {
            const parsedData = JSON.parse(data);
            if (parsedData.content) {
              onChunk(parsedData.content);
            }
          } catch (e) {
            console.error('Error parsing SSE data:', e);
          }
        }

        // Continue reading if not aborted
        if (!signal?.aborted) {
          readStream();
        } else {
          reader.cancel().catch(e => console.error('Error cancelling reader:', e));
          onError(new DOMException('Request aborted', 'AbortError'));
        }
      }).catch(error => {
        // If the error is an AbortError, handle it specially
        if (error.name === 'AbortError') {
          console.log('Fetch aborted');
        } else {
          onError(error);
        }
      });
    }

    readStream();
  })
  .catch(error => {
    // If the error is an AbortError, handle it specially
    if (error.name === 'AbortError') {
      console.log('Fetch aborted');
    } else {
      onError(error);
    }
  });
} 