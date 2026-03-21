import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
    const backendUrl = 'http://backend:8000/api/orders/export-excel/';
    const authHeader = request.headers.get('Authorization');

    const searchParams = request.nextUrl.searchParams.toString();
    const url = searchParams ? `${backendUrl}?${searchParams}` : backendUrl;

    const response = await fetch(url, {
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
            'Content-Disposition': 'attachment; filename="Siparis_Karliligi.xlsx"',
        },
    });
}
