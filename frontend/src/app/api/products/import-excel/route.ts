import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  const backendUrl = 'http://backend:8000/api/products/import-excel/';
  const authHeader = request.headers.get('Authorization');

  let formData: FormData;
  try {
    formData = await request.formData();
  } catch {
    return NextResponse.json({ error: 'Geçersiz istek formatı. Lütfen bir dosya seçin.' }, { status: 400 });
  }

  try {
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: authHeader ? { Authorization: authHeader } : {},
      body: formData,
    });

    const data = await response.json().catch(() => ({ error: 'Sunucu hatası' }));
    return NextResponse.json(data, { status: response.status });
  } catch (err) {
    return NextResponse.json({ error: 'Sunucuya bağlanılamadı.' }, { status: 502 });
  }
}
