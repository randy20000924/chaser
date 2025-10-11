import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

const MCP_SERVER_URL = process.env.MCP_SERVER_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    const { articleId } = await request.json();
    
    if (!articleId) {
      return NextResponse.json({ error: 'Article ID is required' }, { status: 400 });
    }

    // 調用 MCP Server 的 analyze_article 工具
    const response = await axios.post(`${MCP_SERVER_URL}/tools/analyze_article`, {
      article_id: articleId
    });

    return NextResponse.json(response.data);
  } catch (error) {
    console.error('Error getting article analysis:', error);
    return NextResponse.json({ error: 'Failed to get article analysis' }, { status: 500 });
  }
}
