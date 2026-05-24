"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import {
  Truck, Building2, Ruler, Clock, Save, RotateCcw, Upload,
  Percent, Plus, Minus, AlertTriangle, CheckCircle2, RefreshCw,
  FileSpreadsheet, X, ChevronDown, Info
} from "lucide-react";
import { api } from "@/lib/api";
import { toast } from "sonner";

/* ─── types ─── */
interface CargoCompany {
  id: number;
  name: string;
  code: string;
}

interface CargoSettings {
  default_cargo_company: { id: number; name: string; code: string } | null;
  use_order_cargo_company: boolean;
  use_default_if_missing: boolean;
  apply_barem_0_199: boolean;
  apply_barem_200_349: boolean;
  custom_note: string;
  active_company_count: number;
  has_custom_rates: boolean;
  desi_range: number[];
  last_updated: string;
}

interface RateRow {
  desi_kg: number;
  [company: string]: number;
}

/* ─── helpers ─── */
const fmt = (v: number) =>
  new Intl.NumberFormat("tr-TR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(v);

const parsePrice = (s: string): number => {
  const cleaned = s.replace(/\s/g, "").replace(",", ".");
  const n = parseFloat(cleaned);
  return isNaN(n) ? -1 : n;
};

/* ─── component ─── */
export default function CargoSettingsPage() {
  /* state */
  const [settings, setSettings] = useState<CargoSettings | null>(null);
  const [companies, setCompanies] = useState<CargoCompany[]>([]);
  const [rates, setRates] = useState<RateRow[]>([]);
  const [companyNames, setCompanyNames] = useState<string[]>([]);
  const [hasCustom, setHasCustom] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savingRates, setSavingRates] = useState(false);
  const [dirtyRates, setDirtyRates] = useState<Map<string, number>>(new Map());
  const [editingCell, setEditingCell] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  // Bulk update state
  const [bulkCompany, setBulkCompany] = useState("");
  const [bulkDesiStart, setBulkDesiStart] = useState("1");
  const [bulkDesiEnd, setBulkDesiEnd] = useState("20");
  const [bulkType, setBulkType] = useState("percent");
  const [bulkValue, setBulkValue] = useState("");
  const [bulkUpdating, setBulkUpdating] = useState(false);

  // Import state
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importPreview, setImportPreview] = useState<any[] | null>(null);
  const [importing, setImporting] = useState(false);
  const [showImport, setShowImport] = useState(false);

  // Reset state
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [resetting, setResetting] = useState(false);

  /* ─── fetch data ─── */
  const fetchAll = useCallback(async () => {
    try {
      const [settingsRes, companiesRes, ratesRes] = await Promise.all([
        api.get("/settings/cargo/"),
        api.get("/settings/cargo/companies/"),
        api.get("/settings/cargo/rates/"),
      ]);
      setSettings(settingsRes);
      setCompanies(companiesRes.companies);
      setRates(ratesRes.rates);
      setCompanyNames(ratesRes.companies);
      setHasCustom(ratesRes.has_custom_rates);
      setDirtyRates(new Map());
    } catch (err: any) {
      toast.error("Kargo ayarları yüklenemedi", { description: err.message });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  /* ─── save settings ─── */
  const saveSettings = async (patch: Record<string, any>) => {
    setSaving(true);
    try {
      await api.patch("/settings/cargo/", patch);
      toast.success("Kargo ayarları güncellendi");
      const fresh = await api.get("/settings/cargo/");
      setSettings(fresh);
    } catch (err: any) {
      toast.error("Kayıt hatası", { description: err.message });
    } finally {
      setSaving(false);
    }
  };

  /* ─── inline edit handlers ─── */
  const startEdit = (desi: number, company: string, currentVal: number) => {
    const key = `${desi}-${company}`;
    setEditingCell(key);
    setEditValue(fmt(currentVal));
    setTimeout(() => inputRef.current?.select(), 50);
  };

  const commitEdit = (desi: number, company: string) => {
    const price = parsePrice(editValue);
    if (price < 0) {
      toast.error("Geçersiz fiyat değeri");
      setEditingCell(null);
      return;
    }
    const key = `${desi}-${company}`;
    const newDirty = new Map(dirtyRates);
    newDirty.set(key, price);
    setDirtyRates(newDirty);

    // Update local rates display
    setRates((prev) =>
      prev.map((r) => (r.desi_kg === desi ? { ...r, [company]: price } : r))
    );
    setEditingCell(null);
  };

  const cancelEdit = () => {
    setEditingCell(null);
  };

  /* ─── save rates ─── */
  const saveRates = async () => {
    if (dirtyRates.size === 0) {
      toast.info("Değişiklik yok");
      return;
    }
    setSavingRates(true);
    const updates = Array.from(dirtyRates.entries()).map(([key, price]) => {
      const [desi, ...companyParts] = key.split("-");
      return { desi_kg: parseInt(desi), company_name: companyParts.join("-"), price };
    });
    try {
      const res: any = await api.patch("/settings/cargo/rates/", { updates });
      toast.success(`${res.updated_count} fiyat güncellendi`);
      if (res.errors?.length) {
        res.errors.forEach((e: string) => toast.warning(e));
      }
      setDirtyRates(new Map());
      await fetchAll();
    } catch (err: any) {
      toast.error("Kayıt hatası", { description: err.message });
    } finally {
      setSavingRates(false);
    }
  };

  /* ─── bulk update ─── */
  const handleBulkUpdate = async () => {
    if (!bulkCompany || !bulkValue) {
      toast.error("Lütfen firma ve değer girin");
      return;
    }
    setBulkUpdating(true);
    try {
      const res: any = await api.post("/settings/cargo/rates/bulk-update/", {
        company_name: bulkCompany,
        desi_start: parseInt(bulkDesiStart),
        desi_end: parseInt(bulkDesiEnd),
        update_type: bulkType,
        value: bulkValue,
      });
      toast.success(res.message);
      setBulkValue("");
      await fetchAll();
    } catch (err: any) {
      toast.error("Toplu güncelleme hatası", { description: err.message });
    } finally {
      setBulkUpdating(false);
    }
  };

  /* ─── import ─── */
  const handleImportPreview = async () => {
    if (!importFile) return;
    setImporting(true);
    try {
      const formData = new FormData();
      formData.append("file", importFile);
      formData.append("preview", "true");
      const res = await fetch("/api/settings/cargo/rates/import/", {
        method: "POST",
        headers: { Authorization: `Bearer ${localStorage.getItem("access_token")}` },
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Import hatası");
      setImportPreview(data.rows);
      toast.info(`${data.total_rows} satır bulundu — önizleme gösteriliyor`);
    } catch (err: any) {
      toast.error("Dosya okunamadı", { description: err.message });
    } finally {
      setImporting(false);
    }
  };

  const handleImportConfirm = async () => {
    if (!importFile) return;
    setImporting(true);
    try {
      const formData = new FormData();
      formData.append("file", importFile);
      formData.append("preview", "false");
      const res = await fetch("/api/settings/cargo/rates/import/", {
        method: "POST",
        headers: { Authorization: `Bearer ${localStorage.getItem("access_token")}` },
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Import hatası");
      toast.success(`${data.imported_rows} fiyat içe aktarıldı`);
      if (data.failed_rows > 0) {
        toast.warning(`${data.failed_rows} satır hatalı`);
      }
      setImportFile(null);
      setImportPreview(null);
      setShowImport(false);
      await fetchAll();
    } catch (err: any) {
      toast.error("İçe aktarma hatası", { description: err.message });
    } finally {
      setImporting(false);
    }
  };

  /* ─── reset ─── */
  const handleReset = async () => {
    setResetting(true);
    try {
      const res: any = await api.post("/settings/cargo/rates/reset-defaults/", {});
      toast.success(res.message);
      setShowResetConfirm(false);
      await fetchAll();
    } catch (err: any) {
      toast.error("Sıfırlama hatası", { description: err.message });
    } finally {
      setResetting(false);
    }
  };

  /* ─── loading ─── */
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-blue-500 border-t-transparent shadow-lg" />
        <p className="text-slate-400 font-medium animate-pulse">Kargo ayarları yükleniyor...</p>
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <AlertTriangle className="text-yellow-500 w-12 h-12" />
        <p className="text-slate-400">Kargo ayarları yüklenemedi. Sayfayı yenileyin.</p>
      </div>
    );
  }

  const hasDirty = dirtyRates.size > 0;

  return (
    <div className="max-w-[1600px] mx-auto py-6 px-4 sm:px-6 lg:px-8 space-y-6 animate-in fade-in duration-500">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
            Kargo Ayarları
          </h1>
          <p className="text-slate-400 mt-1">
            Kargo firmalarınızı, desi fiyatlarınızı ve barem ayarlarınızı yönetin.
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowImport(!showImport)}
            className="border-slate-700 text-slate-300 hover:bg-slate-800 h-9"
          >
            <Upload className="w-4 h-4 mr-2" /> İçe Aktar
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowResetConfirm(true)}
            className="border-slate-700 text-slate-300 hover:bg-slate-800 h-9"
          >
            <RotateCcw className="w-4 h-4 mr-2" /> Varsayılana Sıfırla
          </Button>
        </div>
      </div>

      {/* ── A: Summary Cards ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          {
            icon: Truck,
            label: "Varsayılan Kargo",
            value: settings.default_cargo_company?.name || "Seçilmedi",
            color: "text-blue-400",
            bg: "bg-blue-500/10 border-blue-500/20",
          },
          {
            icon: Building2,
            label: "Aktif Firma",
            value: `${settings.active_company_count} firma`,
            color: "text-emerald-400",
            bg: "bg-emerald-500/10 border-emerald-500/20",
          },
          {
            icon: Ruler,
            label: "Desi Aralığı",
            value: settings.desi_range.length
              ? `${settings.desi_range[0]} - ${settings.desi_range[settings.desi_range.length - 1]} Desi`
              : "Tanımsız",
            color: "text-amber-400",
            bg: "bg-amber-500/10 border-amber-500/20",
          },
          {
            icon: Clock,
            label: "Son Güncelleme",
            value: new Date(settings.last_updated).toLocaleDateString("tr-TR", {
              day: "2-digit",
              month: "short",
              year: "numeric",
            }),
            color: "text-purple-400",
            bg: "bg-purple-500/10 border-purple-500/20",
          },
        ].map((card, i) => (
          <Card key={i} className="bg-slate-900/80 border-slate-800/60 backdrop-blur-sm">
            <CardContent className="p-4 flex items-center gap-3">
              <div className={`w-10 h-10 rounded-xl ${card.bg} border flex items-center justify-center shrink-0`}>
                <card.icon className={`w-5 h-5 ${card.color}`} />
              </div>
              <div className="min-w-0">
                <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">{card.label}</p>
                <p className="text-sm font-semibold text-white truncate">{card.value}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* ── B: Barem & Default Company Settings ── */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Barem İndirim Ayarları */}
        <Card className="bg-slate-900/80 border-slate-800/60">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg text-white flex items-center gap-2">
              <Percent className="w-5 h-5 text-blue-400" />
              Kargo Barem İndirim Ayarları
            </CardTitle>
            <CardDescription className="text-slate-400">
              Kâr hesabında Trendyol kargo barem desteğinin uygulanıp uygulanmayacağını belirleyin.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/50 border border-slate-800/50">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white">0₺ - 199,99₺ Barem İndirimi</p>
                <p className="text-xs text-slate-500 mt-0.5">Bu fiyat aralığında Trendyol'un kargo barem desteğini uygula</p>
              </div>
              <Switch
                checked={settings.apply_barem_0_199}
                onCheckedChange={(v) => {
                  setSettings({ ...settings, apply_barem_0_199: v });
                  saveSettings({ apply_barem_0_199: v });
                }}
                disabled={saving}
              />
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/50 border border-slate-800/50">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white">200₺ - 349,99₺ Barem İndirimi</p>
                <p className="text-xs text-slate-500 mt-0.5">Bu fiyat aralığında Trendyol'un kargo barem desteğini uygula</p>
              </div>
              <Switch
                checked={settings.apply_barem_200_349}
                onCheckedChange={(v) => {
                  setSettings({ ...settings, apply_barem_200_349: v });
                  saveSettings({ apply_barem_200_349: v });
                }}
                disabled={saving}
              />
            </div>
          </CardContent>
        </Card>

        {/* Varsayılan Kargo Firması */}
        <Card className="bg-slate-900/80 border-slate-800/60">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg text-white flex items-center gap-2">
              <Truck className="w-5 h-5 text-emerald-400" />
              Varsayılan Kargo Firması
            </CardTitle>
            <CardDescription className="text-slate-400">
              Sipariş verisinde kargo firması belirtilmezse hangi firmanın kullanılacağını seçin.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div>
              <Label className="text-slate-300 text-sm mb-2 block">Kargo Firması</Label>
              <Select
                value={settings.default_cargo_company?.id?.toString() || ""}
                onValueChange={(v) => {
                  saveSettings({ default_cargo_company_id: v ? parseInt(v) : null });
                }}
              >
                <SelectTrigger className="bg-slate-950/50 border-slate-700 text-white h-10">
                  <SelectValue placeholder="Firma seçin..." />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-700">
                  {companies.map((c) => (
                    <SelectItem key={c.id} value={c.id.toString()} className="text-white hover:bg-slate-800">
                      {c.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/50 border border-slate-800/50">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white">Siparişteki firmayı kullan</p>
                  <p className="text-xs text-slate-500 mt-0.5">Trendyol siparişinden kargo firması gelirse onu kullan</p>
                </div>
                <Switch
                  checked={settings.use_order_cargo_company}
                  onCheckedChange={(v) => {
                    setSettings({ ...settings, use_order_cargo_company: v });
                    saveSettings({ use_order_cargo_company: v });
                  }}
                  disabled={saving}
                />
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/50 border border-slate-800/50">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white">Gelmezse varsayılanı kullan</p>
                  <p className="text-xs text-slate-500 mt-0.5">Sipariş verisinde firma yoksa seçili varsayılan firmayı kullan</p>
                </div>
                <Switch
                  checked={settings.use_default_if_missing}
                  onCheckedChange={(v) => {
                    setSettings({ ...settings, use_default_if_missing: v });
                    saveSettings({ use_default_if_missing: v });
                  }}
                  disabled={saving}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ── E: Bulk Update Panel ── */}
      <Card className="bg-slate-900/80 border-slate-800/60">
        <CardHeader className="pb-4">
          <CardTitle className="text-lg text-white flex items-center gap-2">
            <RefreshCw className="w-5 h-5 text-amber-400" />
            Toplu Fiyat Güncelleme
          </CardTitle>
          <CardDescription className="text-slate-400">
            Seçili firma ve desi aralığı için toplu fiyat güncellemesi yapın.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid sm:grid-cols-2 lg:grid-cols-6 gap-3 items-end">
            <div>
              <Label className="text-slate-400 text-xs mb-1 block">Kargo Firması</Label>
              <Select value={bulkCompany} onValueChange={setBulkCompany}>
                <SelectTrigger className="bg-slate-950/50 border-slate-700 text-white h-9 text-sm">
                  <SelectValue placeholder="Firma" />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-700">
                  {companyNames.map((c) => (
                    <SelectItem key={c} value={c} className="text-white hover:bg-slate-800 text-sm">{c}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-slate-400 text-xs mb-1 block">Başlangıç Desi</Label>
              <Input value={bulkDesiStart} onChange={(e) => setBulkDesiStart(e.target.value)}
                className="bg-slate-950/50 border-slate-700 text-white h-9 text-sm" type="number" min="1" max="20" />
            </div>
            <div>
              <Label className="text-slate-400 text-xs mb-1 block">Bitiş Desi</Label>
              <Input value={bulkDesiEnd} onChange={(e) => setBulkDesiEnd(e.target.value)}
                className="bg-slate-950/50 border-slate-700 text-white h-9 text-sm" type="number" min="1" max="20" />
            </div>
            <div>
              <Label className="text-slate-400 text-xs mb-1 block">Güncelleme Tipi</Label>
              <Select value={bulkType} onValueChange={setBulkType}>
                <SelectTrigger className="bg-slate-950/50 border-slate-700 text-white h-9 text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-700">
                  <SelectItem value="percent" className="text-white hover:bg-slate-800 text-sm">% Zam/İndirim</SelectItem>
                  <SelectItem value="fixed" className="text-white hover:bg-slate-800 text-sm">Sabit TL Ekle/Çıkar</SelectItem>
                  <SelectItem value="set" className="text-white hover:bg-slate-800 text-sm">Yeni Fiyat Belirle</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-slate-400 text-xs mb-1 block">Değer</Label>
              <Input value={bulkValue} onChange={(e) => setBulkValue(e.target.value)}
                placeholder={bulkType === "percent" ? "ör: 10" : "ör: 5.00"}
                className="bg-slate-950/50 border-slate-700 text-white h-9 text-sm" />
            </div>
            <Button onClick={handleBulkUpdate} disabled={bulkUpdating}
              className="bg-amber-600 hover:bg-amber-700 text-white h-9 text-sm">
              {bulkUpdating ? <RefreshCw className="w-4 h-4 animate-spin mr-1" /> : null}
              Uygula
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* ── D: Rate Grid ── */}
      <Card className="bg-slate-900/80 border-slate-800/60">
        <CardHeader className="pb-3 flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-lg text-white flex items-center gap-2">
              <FileSpreadsheet className="w-5 h-5 text-blue-400" />
              Kargo Fiyat Tablosu
              {!hasCustom && (
                <span className="text-xs bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded-full ml-2">Varsayılan</span>
              )}
              {hasCustom && (
                <span className="text-xs bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded-full ml-2">Özel</span>
              )}
            </CardTitle>
            <CardDescription className="text-slate-400">
              Hücrelere tıklayarak fiyatları düzenleyin. KDV dahil TL cinsinden.
            </CardDescription>
          </div>
          {hasDirty && (
            <Button onClick={saveRates} disabled={savingRates}
              className="bg-blue-600 hover:bg-blue-700 text-white h-9 text-sm shadow-lg shadow-blue-500/20">
              {savingRates ? <RefreshCw className="w-4 h-4 animate-spin mr-1.5" /> : <Save className="w-4 h-4 mr-1.5" />}
              {dirtyRates.size} Değişikliği Kaydet
            </Button>
          )}
        </CardHeader>
        <CardContent className="p-0">
          {/* Unsaved warning */}
          {hasDirty && (
            <div className="mx-4 mb-3 p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
              <p className="text-xs text-amber-300">
                {dirtyRates.size} hücrede kaydedilmemiş değişiklik var. Sayfayı kapatmadan önce kaydetmeyi unutmayın.
              </p>
            </div>
          )}

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800">
                  <th className="sticky left-0 z-10 bg-slate-900 px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider w-20">
                    Desi
                  </th>
                  {companyNames.map((name) => (
                    <th key={name} className="px-3 py-3 text-center text-xs font-semibold text-slate-400 uppercase tracking-wider whitespace-nowrap min-w-[100px]">
                      {name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rates.map((row, rowIdx) => (
                  <tr key={row.desi_kg} className={`border-b border-slate-800/50 ${rowIdx % 2 === 0 ? "bg-slate-950/30" : ""} hover:bg-slate-800/30 transition-colors`}>
                    <td className="sticky left-0 z-10 bg-slate-900 px-4 py-2.5 font-mono font-semibold text-slate-300 text-center">
                      {row.desi_kg}
                    </td>
                    {companyNames.map((company) => {
                      const cellKey = `${row.desi_kg}-${company}`;
                      const val = row[company] ?? 0;
                      const isDirty = dirtyRates.has(cellKey);
                      const isEditing = editingCell === cellKey;

                      if (isEditing) {
                        return (
                          <td key={company} className="px-1 py-1">
                            <Input
                              ref={inputRef}
                              value={editValue}
                              onChange={(e) => setEditValue(e.target.value)}
                              onBlur={() => commitEdit(row.desi_kg, company)}
                              onKeyDown={(e) => {
                                if (e.key === "Enter") commitEdit(row.desi_kg, company);
                                if (e.key === "Escape") cancelEdit();
                              }}
                              className="h-8 text-center text-sm bg-blue-950/50 border-blue-500 text-white font-mono w-full"
                              autoFocus
                            />
                          </td>
                        );
                      }

                      return (
                        <td
                          key={company}
                          onClick={() => startEdit(row.desi_kg, company, val)}
                          className={`px-3 py-2.5 text-center font-mono text-sm cursor-pointer transition-all
                            ${isDirty
                              ? "bg-amber-500/15 text-amber-200 font-semibold"
                              : "text-slate-300 hover:bg-blue-500/10 hover:text-blue-300"
                            }`}
                        >
                          {fmt(val)}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* ── F: Import Panel (conditionally shown) ── */}
      {showImport && (
        <Card className="bg-slate-900/80 border-slate-800/60">
          <CardHeader className="pb-4 flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-lg text-white flex items-center gap-2">
                <Upload className="w-5 h-5 text-emerald-400" />
                Excel / CSV İçe Aktar
              </CardTitle>
              <CardDescription className="text-slate-400">
                Beklenen kolonlar: Desi/KG, Aras, DHL eCommerce, Kolay Gelsin, PTT, Sürat, TEX, Yurtiçi, CEVA Tedarik, CEVA, Horoz
              </CardDescription>
            </div>
            <Button variant="ghost" size="sm" onClick={() => { setShowImport(false); setImportPreview(null); setImportFile(null); }}>
              <X className="w-4 h-4" />
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="border-2 border-dashed border-slate-700 rounded-xl p-8 text-center hover:border-blue-500/50 transition-colors">
              <input
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={(e) => { setImportFile(e.target.files?.[0] || null); setImportPreview(null); }}
                className="hidden"
                id="cargo-import-file"
              />
              <label htmlFor="cargo-import-file" className="cursor-pointer">
                <FileSpreadsheet className="w-10 h-10 text-slate-500 mx-auto mb-3" />
                <p className="text-sm text-slate-300 font-medium">
                  {importFile ? importFile.name : "Dosyayı sürükleyin veya tıklayın"}
                </p>
                <p className="text-xs text-slate-500 mt-1">CSV, XLSX veya XLS formatı</p>
              </label>
            </div>

            {importFile && !importPreview && (
              <Button onClick={handleImportPreview} disabled={importing}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white">
                {importing ? <RefreshCw className="w-4 h-4 animate-spin mr-2" /> : null}
                Önizleme Göster
              </Button>
            )}

            {importPreview && (
              <>
                <div className="overflow-x-auto max-h-64 rounded-lg border border-slate-800">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="bg-slate-800">
                        {Object.keys(importPreview[0] || {}).map((k) => (
                          <th key={k} className="px-3 py-2 text-slate-400 text-left whitespace-nowrap">{k}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {importPreview.slice(0, 10).map((row, i) => (
                        <tr key={i} className="border-t border-slate-800/50">
                          {Object.values(row).map((v: any, j) => (
                            <td key={j} className="px-3 py-1.5 text-slate-300 whitespace-nowrap">{String(v ?? "")}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <Button onClick={handleImportConfirm} disabled={importing}
                  className="w-full bg-emerald-600 hover:bg-emerald-700 text-white">
                  {importing ? <RefreshCw className="w-4 h-4 animate-spin mr-2" /> : <CheckCircle2 className="w-4 h-4 mr-2" />}
                  İçe Aktar ve Kaydet
                </Button>
              </>
            )}
          </CardContent>
        </Card>
      )}

      {/* ── G: Reset Confirmation Dialog ── */}
      {showResetConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <Card className="bg-slate-900 border-slate-700 w-full max-w-md mx-4 shadow-2xl">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-400" />
                Varsayılana Sıfırla
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-slate-300">
                Mevcut satıcıya özel kargo fiyatlarınız silinecek ve varsayılan Trendyol kargo fiyatları yüklenecek.
                <strong className="text-amber-300"> Bu işlem geri alınamaz.</strong>
              </p>
              <div className="flex gap-3 justify-end">
                <Button variant="outline" onClick={() => setShowResetConfirm(false)}
                  className="border-slate-700 text-slate-300 hover:bg-slate-800">
                  İptal
                </Button>
                <Button onClick={handleReset} disabled={resetting}
                  className="bg-red-600 hover:bg-red-700 text-white">
                  {resetting ? <RefreshCw className="w-4 h-4 animate-spin mr-2" /> : <RotateCcw className="w-4 h-4 mr-2" />}
                  Evet, Sıfırla
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
