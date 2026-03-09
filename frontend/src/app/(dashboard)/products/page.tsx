"use client";

import React, { useState, useEffect } from "react";
import Image from "next/image";
import { api } from "@/lib/api";
import { toast } from "sonner";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Package, Search, Save, RefreshCw, ChevronDown, ChevronUp, Copy, CheckCircle2, Check, FileDown, FileUp } from "lucide-react";

interface Variant {
    id: number;
    title: string;
    barcode: string;
    cost_price: string;
    cost_vat_rate: string;
    desi: string | null;
}

interface Product {
    id: number;
    title: string;
    barcode: string;
    marketplace_sku: string;
    sale_price: string;
    vat_rate: string;
    commission_rate: string;
    image_url: string;
    desi: string;
    default_carrier: string;
    brand: string;
    return_rate: string;
    fast_delivery: boolean;
    is_active: boolean;
    variants: Variant[];
}

export default function ProductsPage() {
    const [products, setProducts] = useState<Product[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState("");
    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);

    // UI states
    const [expandedRows, setExpandedRows] = useState<Record<number, boolean>>({});
    const [updatingVariantId, setUpdatingVariantId] = useState<number | null>(null);
    const [updatingProductId, setUpdatingProductId] = useState<number | null>(null);
    const [copiedBarcode, setCopiedBarcode] = useState<string | null>(null);
    const [isExporting, setIsExporting] = useState(false);
    const [isImporting, setIsImporting] = useState(false);
    const fileInputRef = React.useRef<HTMLInputElement>(null);

    const fetchProducts = async (currentPage = page, search = searchTerm) => {
        setIsLoading(true);
        try {
            const res: any = await api.get(`/products/?page=${currentPage}&search=${search}`);
            setProducts(res.results || []);
            setTotalCount(res.count || 0);
        } catch (error) {
            console.error("Failed to load products:", error);
            toast.error("Ürünler yüklenemedi.");
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
                setPage(1); // this will trigger the fetch in the other effect
            } else {
                fetchProducts(1, searchTerm);
            }
        }, 600);
        return () => clearTimeout(timer);
    }, [searchTerm]);

    // Filter - Server side handles it now
    const filteredProducts = products;

    const toggleRow = (productId: number) => {
        setExpandedRows(prev => ({ ...prev, [productId]: !prev[productId] }));
    };

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
        setCopiedBarcode(text);
        setTimeout(() => setCopiedBarcode(null), 2000);
        toast.success("Barkod kopyalandı.");
    };

    const handleVariantChange = (productId: number, variantId: number, field: keyof Variant, value: string) => {
        setProducts(prev => prev.map(p => {
            if (p.id === productId) {
                return {
                    ...p,
                    variants: p.variants.map(v => v.id === variantId ? { ...v, [field]: value } : v)
                };
            }
            return p;
        }));
    };

    const handleProductChange = (productId: number, field: keyof Product, value: any) => {
        setProducts(prev => prev.map(p => (p.id === productId ? { ...p, [field]: value } : p)));
    };

    const saveVariant = async (variant: Variant) => {
        setUpdatingVariantId(variant.id);
        try {
            await api.patch("/products/", {
                variant_id: variant.id,
                cost_price: variant.cost_price,
                cost_vat_rate: variant.cost_vat_rate,
                desi: variant.desi
            });
            toast.success("Varyant maliyeti kaydedildi.");
        } catch (error) {
            console.error(error);
            toast.error("Varyant güncellenirken hata oluştu.");
        } finally {
            setUpdatingVariantId(null);
        }
    };

    const saveProduct = async (product: Product, showToast = true) => {
        setUpdatingProductId(product.id);
        try {
            await api.patch("/products/", {
                id: product.id,
                desi: product.desi,
                vat_rate: product.vat_rate,
                return_rate: product.return_rate,
                fast_delivery: product.fast_delivery
            });
            if (showToast) toast.success("Ürün ayarları kaydedildi.");
        } catch (error) {
            console.error(error);
            if (showToast) toast.error("Ürün güncellenirken hata.");
        } finally {
            setUpdatingProductId(null);
        }
    };

    const toggleFastDelivery = async (productId: number, currentValue: boolean) => {
        const newValue = !currentValue;
        handleProductChange(productId, "fast_delivery", newValue);
        // Doğrudan kaydet
        const product = products.find(p => p.id === productId);
        if (product) {
            const tempProduct = { ...product, fast_delivery: newValue };
            await saveProduct(tempProduct, false);
            toast.success(`Bugün kargoda durumu ${newValue ? 'Aktif' : 'Kapalı'} olarak güncellendi.`);
        }
    };

    const handleExport = async () => {
        setIsExporting(true);
        try {
            const token = localStorage.getItem("access_token");
            const API_BASE = process.env.NEXT_PUBLIC_API_BASE || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

            const response = await fetch(`${API_BASE}/products/export-excel/`, {
                headers: {
                    ...(token ? { Authorization: `Bearer ${token}` } : {})
                }
            });

            if (!response.ok) throw new Error("İndirme başarısız");

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "Urun_Maliyetleri.xlsx";
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            toast.success("Excel başarıyla indirildi.");
        } catch (error) {
            console.error(error);
            toast.error("Excel indirilirken bir hata oluştu.");
        } finally {
            setIsExporting(false);
        }
    };

    const handleImportFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setIsImporting(true);
        const formData = new FormData();
        formData.append("file", file);

        try {
            const token = localStorage.getItem("access_token");
            const API_BASE = process.env.NEXT_PUBLIC_API_BASE || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

            const response = await fetch(`${API_BASE}/products/import-excel/`, {
                method: "POST",
                headers: {
                    ...(token ? { Authorization: `Bearer ${token}` } : {})
                },
                body: formData
            });

            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.error || "Yükleme başarısız");
            }

            const data = await response.json();
            toast.success(data.message || "Excel başarıyla yüklendi.");
            // Reset page and refetch
            setPage(1);
            fetchProducts(1, searchTerm);
        } catch (error: any) {
            console.error(error);
            toast.error(error.message || "Excel yüklenirken bir hata oluştu.");
        } finally {
            setIsImporting(false);
            if (fileInputRef.current) {
                fileInputRef.current.value = "";
            }
        }
    };

    return (
        <div className="flex-1 space-y-4 p-4 animate-in fade-in duration-500">
            {/* Header Banner - Dark Theme */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight text-white flex items-center gap-2">
                        <Package className="text-orange-500" /> Ürün Ayarları
                    </h2>
                    <p className="text-slate-400 mt-1">Gelişmiş analizler için varyant bazlı ürün maliyetlerini, desi ve iade oranlarını ayarlayın.</p>
                </div>
            </div>

            {/* Advanced Filters Block - Dark Theme */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-2xl overflow-hidden mb-6">
                {/* Top Controls */}
                <div className="p-4 border-b border-slate-800 flex flex-col sm:flex-row gap-4 justify-between items-center bg-slate-900/50">
                    <div className="relative w-full sm:w-[400px]">
                        <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-slate-500">
                            <Search size={16} />
                        </div>
                        <Input
                            placeholder="Ürün adı, barkod, model kodu veya marka ara..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="pl-9 h-10 bg-slate-950/50 border-slate-800 focus-visible:ring-orange-500 text-slate-200"
                        />
                    </div>
                    <div className="flex items-center gap-2">
                        <Button variant="outline" onClick={() => fetchProducts(page, searchTerm)} disabled={isLoading} className="border-slate-700 text-slate-300 hover:text-white shrink-0 bg-slate-800 h-10">
                            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                            Yenile
                        </Button>
                        <Button
                            onClick={() => fileInputRef.current?.click()}
                            disabled={isImporting}
                            className="bg-slate-800 hover:bg-slate-700 text-slate-300 shadow-sm h-10 border border-slate-700"
                        >
                            {isImporting ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <FileUp className="w-4 h-4 mr-2" />}
                            Excel Yükle
                        </Button>
                        <input
                            type="file"
                            accept=".xlsx, .xls"
                            className="hidden"
                            ref={fileInputRef}
                            onChange={handleImportFileChange}
                        />
                        <Button
                            onClick={handleExport}
                            disabled={isExporting}
                            className="bg-green-600 hover:bg-green-700 text-white shadow-sm h-10"
                        >
                            {isExporting ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <FileDown className="w-4 h-4 mr-2" />}
                            Excel İndir
                        </Button>
                    </div>
                </div>

                <div className="overflow-x-auto w-full">
                    <Table className="w-full text-sm">
                        <TableHeader className="bg-slate-950/60 sticky top-0 z-10 box-border">
                            <TableRow className="border-slate-800 hover:bg-transparent">
                                <TableHead className="text-slate-400 font-semibold text-center w-20 px-2 py-3">Varyant</TableHead>
                                <TableHead className="text-slate-400 font-semibold px-2">Ürün Bilgisi</TableHead>
                                <TableHead className="text-slate-400 font-semibold text-center px-2">Barkod</TableHead>
                                <TableHead className="text-slate-400 font-semibold text-center w-36 px-2">KDV Dahil Maliyet</TableHead>
                                <TableHead className="text-slate-400 font-semibold text-center w-24 px-2">KDV(%)</TableHead>
                                <TableHead className="text-slate-400 font-semibold text-center w-20 px-2">Desi</TableHead>
                                <TableHead className="text-slate-400 font-semibold text-center px-2 w-28">İade Oranı(%)</TableHead>
                                <TableHead className="text-slate-400 font-semibold text-center w-32 px-2">Bugün Kargoda</TableHead>
                                <TableHead className="text-slate-400 font-semibold text-right pr-4 w-16">İşlem</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {isLoading && products.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={9} className="h-32 text-center text-slate-500">
                                        <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-slate-600" />
                                        Yükleniyor...
                                    </TableCell>
                                </TableRow>
                            ) : filteredProducts.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={9} className="h-32 text-center text-slate-500">
                                        Ürün bulunamadı.
                                    </TableCell>
                                </TableRow>
                            ) : (
                                (() => {
                                    // Group products by marketplace_sku (Model Kodu)
                                    const groups: Record<string, { id: string, master: Product, children: Product[] }> = {};
                                    filteredProducts.forEach(p => {
                                        const key = p.marketplace_sku || `single_${p.id}`;
                                        if (!groups[key]) {
                                            groups[key] = { id: key, master: p, children: [] };
                                        }
                                        groups[key].children.push(p);
                                    });

                                    return Object.values(groups).map((group) => {
                                        const master = group.master;
                                        const children = group.children;
                                        const isExpanded = expandedRows[master.id] || false;
                                        const totalVariants = children.reduce((acc, c) => acc + c.variants.length, 0);

                                        return (
                                            <React.Fragment key={`group-${group.id}`}>
                                                {/* Master Row */}
                                                <TableRow className="bg-slate-900 border-b border-slate-800">
                                                    <TableCell className="text-center px-2">
                                                        <button
                                                            onClick={() => toggleRow(master.id)}
                                                            className={`flex items-center justify-center gap-1.5 rounded-full mx-auto py-1 px-3 transition-all border ${isExpanded ? 'bg-orange-500 text-white border-orange-400 shadow-sm shadow-orange-500/20' : 'bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 border-slate-700'}`}
                                                            title="Varyantları Düzenle"
                                                        >
                                                            <span className="font-bold text-sm leading-none">{totalVariants}</span>
                                                            <span className="text-[11px] font-medium leading-none">Varyant</span>
                                                            {isExpanded ? <ChevronUp size={14} className="opacity-70" /> : <ChevronDown size={14} className="opacity-70" />}
                                                        </button>
                                                    </TableCell>
                                                    <TableCell className="px-2 min-w-[320px]">
                                                        <div className="flex items-center gap-3">
                                                            <div className="w-10 h-10 rounded-md overflow-hidden relative border border-slate-700 shrink-0 bg-slate-800">
                                                                {master.image_url ? (
                                                                    <Image src={master.image_url} alt={master.title} fill className="object-cover" />
                                                                ) : (
                                                                    <Package className="w-6 h-6 text-slate-600 absolute inset-0 m-auto" />
                                                                )}
                                                            </div>
                                                            <div className="min-w-0 flex-1">
                                                                <div className="font-semibold text-slate-200 text-[13px] line-clamp-1 cursor-pointer hover:text-orange-400 transition-colors" title={master.title} onClick={() => toggleRow(master.id)}>
                                                                    {master.title.split('-')[0].trim()}
                                                                </div>
                                                                <div className="text-[11px] text-slate-400 mt-1 flex flex-wrap items-center gap-x-2 gap-y-0.5">
                                                                    <span>Model Kodu: <span className="text-slate-200">{master.marketplace_sku || "-"}</span></span>
                                                                    <span className="text-slate-600 hidden sm:inline">•</span>
                                                                    <span>Marka: <span className="text-slate-200">{master.brand || "EcomMarj"}</span></span>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </TableCell>
                                                    <TableCell className="text-center text-slate-600">---</TableCell>
                                                    <TableCell className="text-center text-slate-600">---</TableCell>
                                                    <TableCell className="px-2">
                                                        <div className="flex justify-center">
                                                            <Input
                                                                type="number" step="1"
                                                                className="w-16 text-center h-8 bg-slate-950 border-slate-700 text-slate-300 text-sm focus-visible:ring-orange-500/50"
                                                                value={master.vat_rate}
                                                                onChange={(e) => handleProductChange(master.id, "vat_rate", e.target.value)}
                                                            />
                                                        </div>
                                                    </TableCell>
                                                    <TableCell className="text-center px-2">
                                                        <Input
                                                            type="number" step="0.1"
                                                            className="w-14 text-center h-8 bg-slate-950 border-slate-700 text-slate-300 text-sm focus-visible:ring-orange-500/50 mx-auto"
                                                            value={master.desi}
                                                            onChange={(e) => handleProductChange(master.id, "desi", e.target.value)}
                                                        />
                                                    </TableCell>
                                                    <TableCell className="text-center px-2">
                                                        <Input
                                                            type="number" step="0.01"
                                                            className="w-16 text-center h-8 bg-slate-950 border-slate-700 text-slate-300 text-sm focus-visible:ring-orange-500/50 mx-auto"
                                                            value={master.return_rate}
                                                            onChange={(e) => handleProductChange(master.id, "return_rate", e.target.value)}
                                                        />
                                                    </TableCell>
                                                    <TableCell className="px-2 text-center align-middle">
                                                        <div className="flex items-center justify-center gap-2">
                                                            <Switch
                                                                checked={master.fast_delivery}
                                                                onCheckedChange={() => toggleFastDelivery(master.id, master.fast_delivery)}
                                                            />
                                                            <span className={`text-[11px] font-medium ${master.fast_delivery ? 'text-green-400' : 'text-slate-500'}`}>
                                                                {master.fast_delivery ? 'Açık' : 'Kapalı'}
                                                            </span>
                                                        </div>
                                                    </TableCell>
                                                    <TableCell className="text-right pr-4 px-2">
                                                        <Button
                                                            size="icon"
                                                            onClick={() => saveProduct(master)}
                                                            disabled={updatingProductId === master.id}
                                                            className="h-8 w-8 bg-orange-500/10 text-orange-500 hover:bg-orange-500 hover:text-white border border-orange-500/20"
                                                        >
                                                            {updatingProductId === master.id ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                                        </Button>
                                                    </TableCell>
                                                </TableRow>

                                                {/* Variants */}
                                                {isExpanded && children.map(child => (
                                                    child.variants.map((v) => (
                                                        <TableRow key={`var-${v.id}`} className="bg-slate-900/40 hover:bg-slate-800/50 border-b border-slate-800/50 transition-colors">
                                                            <TableCell className="relative px-2">
                                                                <div className="absolute top-0 left-1/2 w-px h-full bg-slate-700 -translate-x-1/2"></div>
                                                                {/* T-Shape / L-Shape Connector Logic for exact UI match */}
                                                                <div className="absolute top-1/2 left-1/2 w-4 h-px bg-slate-700"></div>
                                                            </TableCell>
                                                            <TableCell className="px-2 max-w-[280px]">
                                                                <div className="flex items-center gap-3 pl-6">
                                                                    <div className="w-8 h-8 rounded shrink-0 overflow-hidden relative border border-slate-700 bg-slate-800">
                                                                        {child.image_url ? (
                                                                            <Image src={child.image_url} alt={child.title} fill className="object-cover" />
                                                                        ) : (
                                                                            <Package className="w-4 h-4 text-slate-600 absolute inset-0 m-auto" />
                                                                        )}
                                                                    </div>
                                                                    <div className="min-w-0 flex-1">
                                                                        <div className="font-medium text-slate-300 text-[12px] truncate line-clamp-2 leading-tight" title={child.title}>{child.title}</div>
                                                                    </div>
                                                                </div>
                                                            </TableCell>
                                                            <TableCell className="text-center px-2">
                                                                <div className="flex items-center justify-center gap-2 mx-auto">
                                                                    <span className="font-mono text-[12px] text-slate-300 bg-slate-800 px-2 py-1 rounded border border-slate-700 w-full truncate cursor-pointer hover:bg-slate-700 transition-colors" title="Büyütüp kopyalamak için tıklayın" onClick={() => copyToClipboard(v.barcode)}>
                                                                        {v.barcode}
                                                                    </span>
                                                                    <button
                                                                        onClick={() => copyToClipboard(v.barcode)}
                                                                        className={`shrink-0 p-1.5 rounded-md transition-colors ${copiedBarcode === v.barcode ? 'bg-green-500/20 text-green-400' : 'bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700'} border border-slate-700`}
                                                                        title="Barkodu Kopyala"
                                                                    >
                                                                        {copiedBarcode === v.barcode ? <Check size={14} /> : <Copy size={14} />}
                                                                    </button>
                                                                </div>
                                                            </TableCell>
                                                            <TableCell className="px-2">
                                                                <div className="flex items-center justify-center gap-2">
                                                                    <Input
                                                                        type="number" step="0.01"
                                                                        className="w-20 text-center h-8 bg-slate-950 border-orange-500/50 text-orange-50 text-sm focus-visible:ring-orange-500/50 placeholder:text-slate-600"
                                                                        placeholder="Maliyet"
                                                                        value={v.cost_price}
                                                                        onChange={(e) => handleVariantChange(child.id, v.id, "cost_price", e.target.value)}
                                                                    />
                                                                    <span className="text-slate-500 text-xs font-medium">TRY</span>
                                                                </div>
                                                            </TableCell>
                                                            <TableCell className="px-2">
                                                                <div className="flex justify-center">
                                                                    <Input
                                                                        type="number" step="1"
                                                                        className="w-16 text-center h-8 bg-slate-950 border-slate-700 text-slate-300 text-sm focus-visible:ring-orange-500/50"
                                                                        value={v.cost_vat_rate}
                                                                        onChange={(e) => handleVariantChange(child.id, v.id, "cost_vat_rate", e.target.value)}
                                                                    />
                                                                </div>
                                                            </TableCell>
                                                            <TableCell className="px-2 text-center text-slate-500 relative">
                                                                <div className="flex justify-center">
                                                                    <Input
                                                                        type="number" step="0.1"
                                                                        className="w-14 text-center h-8 bg-slate-950 border-slate-700 text-slate-300 text-sm focus-visible:ring-orange-500/50"
                                                                        value={v.desi || child.desi}
                                                                        onChange={(e) => handleVariantChange(child.id, v.id, "desi", e.target.value)}
                                                                    />
                                                                </div>
                                                            </TableCell>
                                                            <TableCell className="text-center text-slate-600">---</TableCell>
                                                            <TableCell className="text-center text-slate-600">---</TableCell>
                                                            <TableCell className="text-right pr-4 px-2">
                                                                <Button
                                                                    size="icon"
                                                                    onClick={async () => {
                                                                        await saveVariant(v);
                                                                    }}
                                                                    disabled={updatingVariantId === v.id}
                                                                    className="h-8 w-8 bg-orange-500/10 text-orange-500 hover:bg-orange-500 hover:text-white border border-orange-500/20"
                                                                >
                                                                    {updatingVariantId === v.id ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                                                </Button>
                                                            </TableCell>
                                                        </TableRow>
                                                    ))
                                                ))}
                                            </React.Fragment>
                                        );
                                    });
                                })()
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
