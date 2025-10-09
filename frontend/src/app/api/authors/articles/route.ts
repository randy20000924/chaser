import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

const MCP_SERVER_URL = process.env.MCP_SERVER_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    const { author } = await request.json();
    
    if (!author) {
      return NextResponse.json({ error: 'Author is required' }, { status: 400 });
    }

    // 調用 MCP Server 的 get_author_articles 工具
    const response = await axios.post(`${MCP_SERVER_URL}/tools/get_author_articles`, {
      author: author,
      limit: 20
    });

    return NextResponse.json(response.data);
  } catch (error) {
    console.error('Error fetching author articles:', error);
    return NextResponse.json({ error: 'Failed to fetch author articles' }, { status: 500 });
  }
}
