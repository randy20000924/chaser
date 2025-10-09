import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

const MCP_SERVER_URL = process.env.MCP_SERVER_URL || 'http://localhost:8000';

export async function GET() {
  try {
    // 調用 MCP Server 的 get_all_authors 工具
    const response = await axios.post(`${MCP_SERVER_URL}/tools/get_all_authors`);

    return NextResponse.json(response.data);
  } catch (error) {
    console.error('Error fetching authors list:', error);
    return NextResponse.json({ error: 'Failed to fetch authors list' }, { status: 500 });
  }
}
