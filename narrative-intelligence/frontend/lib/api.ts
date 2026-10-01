import { AnalyzeResponse } from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function analyzeDocument(text: string, document_id: string): Promise<AnalyzeResponse> {
  try {
    const res = await fetch(`${API_URL}/api/lens/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text, document_id }),
    });

    if (!res.ok) {
      throw new Error(`API Error: ${res.statusText}`);
    }

    const data: AnalyzeResponse = await res.json();
    return data;
  } catch (error) {
    console.error('Error analyzing document:', error);
    return {
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}
