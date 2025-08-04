import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { error, context, userCommand, sessionId } = body;

    // Call the backend's chat endpoint with error analysis context
    const response = await fetch('http://localhost:8000/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: `ANALYSE D'ERREUR - Aide l'utilisateur à résoudre ce problème:

ERREUR: ${error}
COMMANDE UTILISATEUR: ${userCommand}
CONTEXTE: ${context}

En tant qu'expert technique, analyse cette erreur et donne des conseils pratiques à l'utilisateur pour la résoudre. Sois spécifique et utile.`,
        session_id: sessionId
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error getting error help:', error);
    return NextResponse.json(
      { error: 'Failed to get error help' },
      { status: 500 }
    );
  }
} 