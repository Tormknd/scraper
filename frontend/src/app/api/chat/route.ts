import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    const response = await fetch('https://scraper-mq45.onrender.com/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      // Get more detailed error information
      let errorDetails = `HTTP ${response.status}`;
      try {
        const errorBody = await response.text();
        if (errorBody) {
          errorDetails += `: ${errorBody}`;
        }
      } catch (e) {
        // If we can't read the error body, just use the status
      }
      
      throw new Error(`HTTP error! status: ${response.status} - ${errorDetails}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error sending chat message:', error);
    return NextResponse.json(
      { 
        error: 'Failed to send chat message',
        details: error instanceof Error ? error.message : 'Unknown error',
        context: {
          endpoint: '/chat',
          method: 'POST',
          backend_url: 'https://scraper-mq45.onrender.com/chat'
        }
      },
      { status: 500 }
    );
  }
} 