import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

const MCP_SERVER_URL = process.env.MCP_SERVER_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const author = searchParams.get('author');
    
    if (!author) {
      return NextResponse.json({ error: 'Author parameter is required' }, { status: 400 });
    }

    // 調用 MCP Server 的 search_articles 工具
    const response = await axios.post(`${MCP_SERVER_URL}/tools/search_articles`, {
      author: author,
      limit: 50
    });

    return NextResponse.json(response.data);
  } catch (error) {
    console.error('Error fetching author data:', error);
    return NextResponse.json({ error: 'Failed to fetch author data' }, { status: 500 });
  }
}
