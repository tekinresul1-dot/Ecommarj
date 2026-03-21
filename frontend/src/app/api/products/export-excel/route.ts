import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const backendUrl = 'http://backend:8000/api/products/export-excel/';
  const authHeader = request.headers.get('Authorization');

  const response = await fetch(backendUrl, {
    headers: authHeader ? { Authorization: authHeader } : {},
  });

  if (!response.ok) {
    return NextResponse.json({ error: 'Export failed' }, { status: response.status });
  }

  const buffer = await response.arrayBuffer();
  return new NextResponse(buffer, {
    status: 200,
    headers: {
      'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'Content-Disposition': 'attachment; filename="Urun_Maliyetleri.xlsx"',
    },
  });
}
