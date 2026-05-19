import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  const backendUrl = 'http://backend:8000/api/products/import-excel/';
  const authHeader = request.headers.get('Authorization');

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return NextResponse.json({ error: 'Yetkilendirme gerekli.' }, { status: 401 });
  }

  let formData: FormData;
  try {
    formData = await request.formData();
  } catch {
    return NextResponse.json({ error: 'Geçersiz istek formatı. Lütfen bir dosya seçin.' }, { status: 400 });
  }

  // Yüklenen dosyayı backend'e iletmeden önce tip/boyut doğrula
  const file = formData.get('file');
  if (file instanceof File) {
    const MAX_BYTES = 10 * 1024 * 1024; // 10 MB
    const allowed = /\.(xlsx|xls)$/i;
    if (!allowed.test(file.name)) {
      return NextResponse.json({ error: 'Yalnızca .xlsx/.xls dosyaları kabul edilir.' }, { status: 400 });
    }
    if (file.size > MAX_BYTES) {
      return NextResponse.json({ error: 'Dosya boyutu 10 MB sınırını aşıyor.' }, { status: 413 });
    }
  } else {
    return NextResponse.json({ error: 'Bir dosya seçmelisiniz.' }, { status: 400 });
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
