"use client";

import { useState, useEffect } from "react";
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
import { Package, Search, Save, RefreshCw, ChevronDown, ChevronUp, Copy, CheckCircle2 } from "lucide-react";

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

    // UI states
    const [expandedRows, setExpandedRows] = useState<Record<number, boolean>>({});
    const [updatingVariantId, setUpdatingVariantId] = useState<number | null>(null);
    const [updatingProductId, setUpdatingProductId] = useState<number | null>(null);
    const [copiedBarcode, setCopiedBarcode] = useState<string | null>(null);

    const fetchProducts = async () => {
        setIsLoading(true);
        try {
            const res: any = await api.get("/products/");
            setProducts(res.results || []);
        } catch (error) {
            console.error("Failed to load products:", error);
            toast.error("Ürünler yüklenemedi.");
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchProducts();
    }, []);

    // Filter
    const filteredProducts = products.filter((p) =>
        p.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.barcode.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.variants.some(v => v.barcode.toLowerCase().includes(searchTerm.toLowerCase()) || v.title.toLowerCase().includes(searchTerm.toLowerCase()))
    );

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
                        <Button variant="outline" onClick={fetchProducts} disabled={isLoading} className="border-slate-700 text-slate-300 hover:text-white shrink-0 bg-slate-800 h-10">
                            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                            Yenile
                        </Button>
                        <Button className="bg-green-600 hover:bg-green-700 text-white shadow-sm h-10">
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
                                filteredProducts.map((p) => {
                                    const variantCount = p.variants.length;
                                    const isExpanded = expandedRows[p.id] || false;
                                    const hasVariants = variantCount > 1;

                                    // Tek Varyantlı Ürün (Düz Satır)
                                    if (!hasVariants && variantCount === 1) {
                                        const v = p.variants[0];
                                        return (
                                            <TableRow key={p.id} className="border-b border-slate-800 hover:bg-slate-800/30 transition-colors bg-slate-900 group">
                                                <TableCell className="text-center px-2 align-middle">
                                                    <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Tek</span>
                                                </TableCell>
                                                <TableCell className="px-2 max-w-[280px]">
                                                    <div className="flex items-center gap-3">
                                                        <div className="w-10 h-10 rounded-md overflow-hidden relative border border-slate-700 shrink-0 bg-slate-800">
                                                            {p.image_url ? (
                                                                <Image src={p.image_url} alt={p.title} fill className="object-cover" />
                                                            ) : (
                                                                <Package className="w-6 h-6 text-slate-600 absolute inset-0 m-auto" />
                                                            )}
                                                        </div>
                                                        <div className="min-w-0 flex-1">
                                                            <div className="font-semibold text-slate-200 text-[13px] truncate" title={p.title}>{p.title}</div>
                                                            <div className="text-[11px] text-slate-400 mt-0.5 flex items-center gap-2 truncate">
                                                                <span>Kodu: <span className="text-slate-300">{p.marketplace_sku || "-"}</span></span>
                                                                <span className="text-slate-600">|</span>
                                                                <span>Marka: <span className="text-slate-300">{p.brand || "EcomPro"}</span></span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </TableCell>
                                                <TableCell className="px-2">
                                                    <div className="flex items-center justify-center gap-1">
                                                        <div className="border border-slate-700 rounded px-2 py-0.5 text-[11px] text-slate-300 bg-slate-950 font-mono">
                                                            {v.barcode}
                                                        </div>
                                                        <button onClick={() => copyToClipboard(v.barcode)} className="text-slate-500 hover:text-white transition-colors">
                                                            {copiedBarcode === v.barcode ? <CheckCircle2 size={14} className="text-green-500" /> : <Copy size={14} />}
                                                        </button>
                                                    </div>
                                                </TableCell>
                                                <TableCell className="px-2">
                                                    <div className="flex items-center justify-center gap-1">
                                                        <Input
                                                            type="number" step="0.01"
                                                            className="w-20 text-center h-8 bg-slate-950 border-slate-700 text-slate-200 text-sm focus-visible:ring-orange-500/50 font-medium"
                                                            value={v.cost_price}
                                                            onChange={(e) => handleVariantChange(p.id, v.id, "cost_price", e.target.value)}
                                                        />
                                                        <span className="text-[10px] text-slate-500">TRY</span>
                                                    </div>
                                                </TableCell>
                                                <TableCell className="px-2">
                                                    <div className="flex justify-center">
                                                        <Input
                                                            type="number"
                                                            className="w-14 text-center h-8 bg-slate-950 border-slate-700 text-slate-300 text-sm focus-visible:ring-orange-500/50"
                                                            value={v.cost_vat_rate}
                                                            onChange={(e) => handleVariantChange(p.id, v.id, "cost_vat_rate", e.target.value)}
                                                        />
                                                    </div>
                                                </TableCell>
                                                <TableCell className="px-2">
                                                    <div className="flex justify-center">
                                                        <Input
                                                            type="number" step="0.1"
                                                            className="w-14 text-center h-8 bg-slate-950 border-slate-700 text-slate-300 text-sm focus-visible:ring-orange-500/50"
                                                            value={v.desi || p.desi}
                                                            onChange={(e) => handleVariantChange(p.id, v.id, "desi", e.target.value)}
                                                        />
                                                    </div>
                                                </TableCell>
                                                {/* İade Oranı ve Bugün Kargoda (Ürün Bazlı) */}
                                                <TableCell className="px-2">
                                                    <div className="flex justify-center">
                                                        <Input
                                                            type="number" step="0.01"
                                                            className="w-16 text-center h-8 bg-slate-950 border-slate-700 text-slate-300 text-sm focus-visible:ring-orange-500/50"
                                                            value={p.return_rate}
                                                            onChange={(e) => handleProductChange(p.id, "return_rate", e.target.value)}
                                                            placeholder="0.00"
                                                        />
                                                    </div>
                                                </TableCell>
                                                <TableCell className="px-2 text-center align-middle">
                                                    <div className="flex items-center justify-center gap-2">
                                                        <Switch
                                                            checked={p.fast_delivery}
                                                            onCheckedChange={() => toggleFastDelivery(p.id, p.fast_delivery)}
                                                        />
                                                        <span className={`text-[11px] font-medium ${p.fast_delivery ? 'text-green-400' : 'text-slate-500'}`}>
                                                            {p.fast_delivery ? 'Açık' : 'Kapalı'}
                                                        </span>
                                                    </div>
                                                </TableCell>
                                                <TableCell className="text-right pr-4 px-2">
                                                    <Button
                                                        size="icon"
                                                        onClick={async () => {
                                                            await saveVariant(v);
                                                            await saveProduct(p, false); // sessiz kaydet
                                                        }}
                                                        disabled={updatingVariantId === v.id || updatingProductId === p.id}
                                                        className="h-8 w-8 bg-orange-500/10 text-orange-500 hover:bg-orange-500 hover:text-white border border-orange-500/20"
                                                    >
                                                        {(updatingVariantId === v.id || updatingProductId === p.id) ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                                    </Button>
                                                </TableCell>
                                            </TableRow>
                                        )
                                    }

                                    // Çok Varyantlı Ürün (Accordion)
                                    return (
                                        <>
                                            <TableRow key={`main-${p.id}`} className="bg-slate-900 border-b border-slate-800">
                                                <TableCell className="text-center px-2">
                                                    <button
                                                        onClick={() => toggleRow(p.id)}
                                                        className="flex flex-col items-center justify-center bg-orange-500 hover:bg-orange-600 text-white rounded-lg mx-auto py-1 px-3 shadow-sm"
                                                    >
                                                        <div className="flex items-center gap-1 font-bold text-sm">
                                                            <span>{variantCount}</span>
                                                            {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                                                        </div>
                                                    </button>
                                                </TableCell>
                                                <TableCell className="px-2 max-w-[280px]">
                                                    <div className="flex items-center gap-3">
                                                        <div className="w-10 h-10 rounded-md overflow-hidden relative border border-slate-700 shrink-0 bg-slate-800">
                                                            {p.image_url ? (
                                                                <Image src={p.image_url} alt={p.title} fill className="object-cover" />
                                                            ) : (
                                                                <Package className="w-6 h-6 text-slate-600 absolute inset-0 m-auto" />
                                                            )}
                                                        </div>
                                                        <div className="min-w-0 flex-1">
                                                            <div className="font-semibold text-slate-200 text-[13px] truncate cursor-pointer hover:text-orange-400 transition-colors" title={p.title} onClick={() => toggleRow(p.id)}>{p.title}</div>
                                                            <div className="text-[11px] text-slate-400 mt-0.5 flex items-center gap-2 truncate">
                                                                <span>Kodu: <span className="text-slate-300">{p.marketplace_sku || "-"}</span></span>
                                                                <span className="text-slate-600">|</span>
                                                                <span>Marka: <span className="text-slate-300">{p.brand || "EcomPro"}</span></span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </TableCell>
                                                <TableCell className="text-center text-slate-600">---</TableCell>
                                                <TableCell className="text-center px-2">
                                                    <div className="text-orange-400 font-semibold text-sm">Genel Aralık</div>
                                                </TableCell>
                                                <TableCell className="text-center text-slate-600">---</TableCell>
                                                <TableCell className="text-center px-2">
                                                    <Input
                                                        type="number" step="0.1"
                                                        className="w-14 text-center h-8 bg-slate-950 border-slate-700 text-slate-300 text-sm focus-visible:ring-orange-500/50 mx-auto"
                                                        value={p.desi}
                                                        onChange={(e) => handleProductChange(p.id, "desi", e.target.value)}
                                                    />
                                                </TableCell>
                                                <TableCell className="text-center px-2">
                                                    <Input
                                                        type="number" step="0.01"
                                                        className="w-16 text-center h-8 bg-slate-950 border-slate-700 text-slate-300 text-sm focus-visible:ring-orange-500/50 mx-auto"
                                                        value={p.return_rate}
                                                        onChange={(e) => handleProductChange(p.id, "return_rate", e.target.value)}
                                                    />
                                                </TableCell>
                                                <TableCell className="px-2 text-center align-middle">
                                                    <div className="flex items-center justify-center gap-2">
                                                        <Switch
                                                            checked={p.fast_delivery}
                                                            onCheckedChange={() => toggleFastDelivery(p.id, p.fast_delivery)}
                                                        />
                                                        <span className={`text-[11px] font-medium ${p.fast_delivery ? 'text-green-400' : 'text-slate-500'}`}>
                                                            {p.fast_delivery ? 'Açık' : 'Kapalı'}
                                                        </span>
                                                    </div>
                                                </TableCell>
                                                <TableCell className="text-right pr-4 px-2">
                                                    <Button
                                                        size="icon"
                                                        onClick={() => saveProduct(p)}
                                                        disabled={updatingProductId === p.id}
                                                        className="h-8 w-8 bg-orange-500/10 text-orange-500 hover:bg-orange-500 hover:text-white border border-orange-500/20"
                                                    >
                                                        {updatingProductId === p.id ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                                    </Button>
                                                </TableCell>
                                            </TableRow>

                                            {/* Varyant Alt Satırları */}
                                            {isExpanded && p.variants.map((v) => (
                                                <TableRow key={`var-${v.id}`} className="bg-slate-900/40 hover:bg-slate-800/50 border-b border-slate-800/50 transition-colors">
                                                    <TableCell className="relative px-2">
                                                        <div className="absolute top-0 left-1/2 w-px h-full bg-slate-700 -translate-x-1/2"></div>
                                                        <div className="absolute top-1/2 left-1/2 w-4 h-px bg-slate-700"></div>
                                                    </TableCell>
                                                    <TableCell className="pl-6 py-2 px-2">
                                                        <div className="flex items-center gap-2">
                                                            <div className="text-[12px] text-slate-300 line-clamp-1 flex-1 font-medium bg-slate-800/50 py-1 px-2 rounded border border-slate-700/50">
                                                                {(v.title || "").split(" - ").pop() || v.title || p.title}
                                                            </div>
                                                        </div>
                                                    </TableCell>
                                                    <TableCell className="px-2">
                                                        <div className="flex items-center justify-center gap-1">
                                                            <div className="border border-slate-700/80 rounded px-2 py-0.5 text-[11px] text-slate-400 bg-slate-900/80 font-mono tracking-wider">
                                                                {v.barcode}
                                                            </div>
                                                            <button onClick={() => copyToClipboard(v.barcode)} className="text-slate-500 hover:text-orange-400">
                                                                {copiedBarcode === v.barcode ? <CheckCircle2 size={14} className="text-green-500" /> : <Copy size={14} />}
                                                            </button>
                                                        </div>
                                                    </TableCell>
                                                    <TableCell className="px-2">
                                                        <div className="flex items-center justify-center gap-1">
                                                            <Input
                                                                type="number" step="0.01"
                                                                className="w-20 text-center h-7 bg-slate-950 border-slate-700/80 text-slate-300 text-xs focus-visible:ring-orange-500/50"
                                                                value={v.cost_price}
                                                                onChange={(e) => handleVariantChange(p.id, v.id, "cost_price", e.target.value)}
                                                            />
                                                        </div>
                                                    </TableCell>
                                                    <TableCell className="px-2">
                                                        <div className="flex justify-center">
                                                            <Input
                                                                type="number"
                                                                className="w-14 text-center h-7 bg-slate-950 border-slate-700/80 text-slate-400 text-xs focus-visible:ring-orange-500/50"
                                                                value={v.cost_vat_rate}
                                                                onChange={(e) => handleVariantChange(p.id, v.id, "cost_vat_rate", e.target.value)}
                                                            />
                                                        </div>
                                                    </TableCell>
                                                    <TableCell className="px-2">
                                                        <div className="flex justify-center">
                                                            <Input
                                                                type="number" step="0.1"
                                                                className="w-14 text-center h-7 bg-slate-950 border-slate-700/80 text-slate-400 text-xs focus-visible:ring-orange-500/50"
                                                                value={v.desi || ''}
                                                                placeholder={p.desi}
                                                                onChange={(e) => handleVariantChange(p.id, v.id, "desi", e.target.value)}
                                                            />
                                                        </div>
                                                    </TableCell>
                                                    <TableCell className="text-center text-slate-600">---</TableCell>
                                                    <TableCell className="text-center text-slate-600">---</TableCell>
                                                    <TableCell className="text-right pr-4 px-2">
                                                        <Button
                                                            size="icon"
                                                            onClick={() => saveVariant(v)}
                                                            disabled={updatingVariantId === v.id}
                                                            className="h-7 w-7 bg-transparent border border-slate-700 text-slate-400 hover:bg-slate-800 hover:text-white"
                                                        >
                                                            {updatingVariantId === v.id ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />}
                                                        </Button>
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                        </>
                                    );
                                })
                            )}
                        </TableBody>
                    </Table>
                </div>
            </div>
        </div>
    );
}
