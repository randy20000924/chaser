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
      console.error(`Backend API error: ${response.status} ${response.statusText}`);
      return NextResponse.json({ 
        error: `Backend API error: ${response.status}`,
        details: await response.text()
      }, { status: response.status });
    }

    const data = await response.json();
    
    // 確保返回的數據格式符合前端期望
    const formattedData = {
      author: data.author || 'Unknown',
      date: data.date || new Date().toISOString().split('T')[0],
      url: data.url || '',
      recommended_stocks: data.recommended_stocks || [],
      reason: data.reason || 'No analysis available'
    };
    
    return NextResponse.json(formattedData);
  } catch (error) {
    console.error('Error getting article analysis:', error);
    return NextResponse.json({ 
      error: 'Failed to get article analysis',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 });
  }
}
