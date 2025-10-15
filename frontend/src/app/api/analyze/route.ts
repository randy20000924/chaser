import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://www.chaser.cloud/api';

export async function POST(request: NextRequest) {
  try {
    const { articleId } = await request.json();
    
    if (!articleId) {
      return NextResponse.json({ error: 'Article ID is required' }, { status: 400 });
    }

    // 直接從後端 API 獲取分析結果
    const response = await fetch(`${BACKEND_URL}/articles/${articleId}/analysis`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error getting article analysis:', error);
    return NextResponse.json({ error: 'Failed to get article analysis' }, { status: 500 });
  }
}
