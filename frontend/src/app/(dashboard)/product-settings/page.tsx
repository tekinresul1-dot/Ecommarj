"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { Package, Search, Image as ImageIcon, CircleDollarSign, Percent, ShieldAlert } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface Product {
  id: string;
  title: string;
  barcode: string;
  marketplace_sku: string;
  sale_price: string;
  vat_rate: string;
  commission_rate: string;
  image_url: string;
  is_active: boolean;
}

export default function ProductSettingsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  const fetchProducts = async (currentPage = page, search = searchTerm) => {
    try {
      setIsLoading(true);
      const res: any = await api.get(`/products/?page=${currentPage}&search=${search}`);
      const resData = res?.data || res;
      if (resData && resData.results) {
        setProducts(resData.results);
        setTotalCount(resData.count || 0);
      }
    } catch (error: any) {
      console.error("Products fetch error:", error);
      toast.error("Ürünler yüklenirken hata oluştu.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts(page, searchTerm);
  }, [page]);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (page !== 1) {
        setPage(1);
      } else {
        fetchProducts(1, searchTerm);
      }
    }, 600);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  const filteredProducts = products;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Package className="text-emerald-500" /> Ürün Ayarları
          </h1>
          <p className="text-slate-400">Trendyol entegrasyonuyla otomatik çekilen ürün detaylarınızı inceleyin.</p>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="relative w-full max-w-sm">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-4 w-4 text-slate-500" />
            </div>
            <Input
              type="text"
              placeholder="Ürün adı veya barkod ara..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 bg-slate-950 border-slate-800 text-slate-200"
            />
          </div>

          <Badge variant="outline" className="hidden sm:inline-flex bg-slate-950 border-slate-800 text-slate-400">
            Toplam: {totalCount} Ürün
          </Badge>
        </div>

        <div className="overflow-x-auto">
          <Table>
            <TableHeader className="bg-slate-950/50">
              <TableRow className="border-slate-800 hover:bg-transparent">
                <TableHead className="w-[80px] text-slate-400">Görsel</TableHead>
                <TableHead className="text-slate-400">Ürün Bilgileri</TableHead>
                <TableHead className="text-slate-400">
                  <div className="flex items-center gap-1"><CircleDollarSign size={14} /> Satış Fiyatı</div>
                </TableHead>
                <TableHead className="text-slate-400">
                  <div className="flex items-center gap-1"><Percent size={14} /> Komisyon</div>
                </TableHead>
                <TableHead className="text-slate-400">
                  <div className="flex items-center gap-1"><ShieldAlert size={14} /> KDV</div>
                </TableHead>
                <TableHead className="text-right text-slate-400">Durum</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={6} className="h-24 text-center text-slate-500">
                    <div className="flex items-center justify-center gap-2">
                      <div className="h-4 w-4 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent"></div>
                      Yükleniyor...
                    </div>
                  </TableCell>
                </TableRow>
              ) : filteredProducts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="h-24 text-center text-slate-500">
                    Ürün bulunamadı. Ayarlar ekranından Trendyol entegrasyonunu başlattığınıza emin olun.
                  </TableCell>
                </TableRow>
              ) : (
                filteredProducts.map((product) => (
                  <TableRow key={product.id} className="border-slate-800 hover:bg-slate-800/50 transition-colors">
                    <TableCell>
                      {product.image_url ? (
                        <div className="w-12 h-12 rounded bg-white flex items-center justify-center overflow-hidden border border-slate-700">
                          <img src={product.image_url} alt={product.title} className="max-w-full max-h-full object-contain" />
                        </div>
                      ) : (
                        <div className="w-12 h-12 rounded bg-slate-800 flex items-center justify-center border border-slate-700">
                          <ImageIcon className="text-slate-500" size={20} />
                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="font-medium text-slate-200 line-clamp-1" title={product.title}>
                        {product.title}
                      </div>
                      <div className="text-xs text-slate-500 mt-1 flex items-center gap-2">
                        <span>Barkod: <span className="text-slate-400">{product.barcode}</span></span>
                        <span>•</span>
                        <span>SKU: <span className="text-slate-400">{product.marketplace_sku || "-"}</span></span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="font-semibold text-emerald-400">
                        {parseFloat(product.sale_price).toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ₺
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="bg-orange-500/10 text-orange-400 border-orange-500/20">
                        %{product.commission_rate}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="bg-slate-800 text-slate-300 border-slate-700">
                        %{product.vat_rate}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      {product.is_active ? (
                        <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20">Aktif</Badge>
                      ) : (
                        <Badge variant="outline" className="bg-red-500/10 text-red-400 border-red-500/20">Pasif</Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Pagination Controls */}
        <div className="p-4 border-t border-slate-800 flex items-center justify-between bg-slate-900/50">
          <div className="text-sm text-slate-400">
            Toplam <span className="font-semibold text-slate-200">{totalCount}</span> üründen <span className="font-semibold text-slate-200">{totalCount > 0 ? (page - 1) * 50 + 1 : 0}-{Math.min(page * 50, totalCount)}</span> arası gösteriliyor.
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page === 1}
              onClick={() => setPage(page - 1)}
              className="border-slate-700 bg-slate-800 text-slate-300 hover:text-white"
            >
              Önceki
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page * 50 >= totalCount}
              onClick={() => setPage(page + 1)}
              className="border-slate-700 bg-slate-800 text-slate-300 hover:text-white"
            >
              Sonraki
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}