"use client";

import { useState, useEffect } from "react";
import { 
  Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter 
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { 
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue 
} from "@/components/ui/select";
import { 
  AlertCircle, Upload, Download, Trash2, CheckCircle2, RefreshCw, Truck, FileSpreadsheet
} from "lucide-react";
import { api } from "@/lib/api";
import { toast } from "sonner";

interface SettingsData {
  default_cargo_company_id: number | null;
  use_trendyol_real_cargo_if_available: boolean;
  use_custom_cargo_rates: boolean;
  apply_barem_discount_0_199: boolean;
  apply_barem_discount_200_349: boolean;
}

interface CargoRate {
  id: number;
  desi: number;
  price: string;
  source: string;
  updated_at: string;
}

export default function CargoSettingsPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  
  const [companies, setCompanies] = useState<{id: number, name: string}[]>([]);
  const [settings, setSettings] = useState<SettingsData>({
    default_cargo_company_id: null,
    use_trendyol_real_cargo_if_available: true,
    use_custom_cargo_rates: false,
    apply_barem_discount_0_199: true,
    apply_barem_discount_200_349: true,
  });
  
  const [customRates, setCustomRates] = useState<CargoRate[]>([]);
  const [lastUploadDate, setLastUploadDate] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      const [settingsRes, companiesRes, ratesRes] = await Promise.all([
        api.get("/settings/cargo/"),
        api.get("/settings/cargo/companies/"),
        api.get("/settings/cargo/custom-rates/")
      ]);
      
      setSettings(settingsRes as any);
      setCompanies((companiesRes as any).companies || []);
      setCustomRates((ratesRes as any).rates || []);
      setLastUploadDate((ratesRes as any).last_upload_date);
    } catch (error: any) {
      toast.error("Hata", { description: "Kargo ayarları yüklenirken hata oluştu." });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveSettings = async () => {
    try {
      setIsSaving(true);
      await api.patch("/settings/cargo/", settings);
      toast.success("Başarılı", { description: "Kargo ayarları kaydedildi." });
    } catch (error: any) {
      toast.error("Hata", { description: "Ayarlar kaydedilemedi." });
    } finally {
      setIsSaving(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    
    try {
      setIsUploading(true);
      const formData = new FormData();
      formData.append("file", file);
      
      const res: any = await api.post("/settings/cargo/custom-rates/import/", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      
      if (res.status === "success" || res.status === "partial") {
        toast.success("Fiyatlar yüklendi", { 
          description: `${res.imported_rows} fiyat kaydedildi. ${res.failed_rows > 0 ? res.failed_rows + " satır hatalıydı." : ""}`
        });
        fetchData(); // Refresh UI
      } else {
        toast.error("Yükleme başarısız", { description: res.errors?.[0] || "Bir hata oluştu." });
      }
    } catch (error: any) {
      toast.error("Hata", { description: "Dosya yüklenirken hata oluştu." });
    } finally {
      setIsUploading(false);
      e.target.value = ""; // clear input
    }
  };

  const handleResetRates = async () => {
    if (!confirm("Özel fiyatlarınızı silmek istediğinize emin misiniz?")) return;
    
    try {
      await api.delete("/settings/cargo/custom-rates/reset/");
      toast.success("Başarılı", { description: "Özel fiyatlarınız silindi." });
      fetchData();
    } catch (error: any) {
      toast.error("Hata", { description: "İşlem başarısız oldu." });
    }
  };

  const handleDownloadTemplate = () => {
    window.location.href = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/settings/cargo/template/`;
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <RefreshCw className="animate-spin text-orange-500 h-8 w-8" />
      </div>
    );
  }

  return (
    <div className="animate-in fade-in duration-500 space-y-6">
      <Card className="bg-slate-900 border-slate-800/60 shadow-xl overflow-hidden relative">
        <div className="absolute top-0 left-0 w-1 h-full bg-blue-500"></div>
        <CardHeader className="pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/10 rounded-lg">
              <Truck className="h-5 w-5 text-blue-400" />
            </div>
            <div>
              <CardTitle className="text-xl text-white">Genel Kargo Ayarları</CardTitle>
              <CardDescription>Siparişlerinize kargo maliyeti yansıtılırken kullanılacak temel kurallar.</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between p-4 bg-slate-950/50 border border-slate-800 rounded-lg">
            <div className="space-y-0.5 max-w-[70%]">
              <Label className="text-base text-slate-200">Trendyol Kargo Faturasını Kullan</Label>
              <p className="text-sm text-slate-400">Trendyol'dan siparişe ait gerçek kargo faturası gelmişse tahmini maliyet yerine onu kullanır. (Önerilen)</p>
            </div>
            <Switch 
              checked={settings.use_trendyol_real_cargo_if_available}
              onCheckedChange={(v) => setSettings({...settings, use_trendyol_real_cargo_if_available: v})}
              className="data-[state=checked]:bg-blue-500"
            />
          </div>

          <div className="flex items-center justify-between p-4 bg-slate-950/50 border border-slate-800 rounded-lg">
            <div className="space-y-1 w-full max-w-sm">
              <Label className="text-base text-slate-200 block mb-1">Varsayılan Kargo Firması</Label>
              <Select 
                value={settings.default_cargo_company_id?.toString() || "none"}
                onValueChange={(v) => setSettings({...settings, default_cargo_company_id: v === "none" ? null : parseInt(v)})}
              >
                <SelectTrigger className="bg-slate-900 border-slate-700">
                  <SelectValue placeholder="Seçiniz..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Seçilmedi</SelectItem>
                  {companies.map(c => (
                    <SelectItem key={c.id} value={c.id.toString()}>{c.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-slate-500 mt-1">Siparişte firma bilgisi yoksa veya anlaşmanız yoksa bu firma varsayılır.</p>
            </div>
          </div>
          
          <div className="p-4 bg-slate-950/50 border border-slate-800 rounded-lg space-y-4">
            <h4 className="font-medium text-slate-200 mb-2">Trendyol Barem Destek İndirimleri</h4>
            
            <div className="flex items-center justify-between">
              <div className="space-y-0.5 max-w-[70%]">
                <Label className="text-sm text-slate-300">0 - 199 TL Siparişler (Barem Uygula)</Label>
                <p className="text-xs text-slate-500">Trendyol'un 200 TL altı siparişlerde sunduğu düşük kargo tarifelerini tahmini hesaplamalarda uygula.</p>
              </div>
              <Switch 
                checked={settings.apply_barem_discount_0_199}
                onCheckedChange={(v) => setSettings({...settings, apply_barem_discount_0_199: v})}
                className="data-[state=checked]:bg-blue-500"
              />
            </div>
            
            <div className="flex items-center justify-between">
              <div className="space-y-0.5 max-w-[70%]">
                <Label className="text-sm text-slate-300">200 - 349 TL Siparişler (Barem Uygula)</Label>
                <p className="text-xs text-slate-500">Trendyol'un sunduğu orta segment kargo barem desteğini tahmini hesaplamalarda uygula.</p>
              </div>
              <Switch 
                checked={settings.apply_barem_discount_200_349}
                onCheckedChange={(v) => setSettings({...settings, apply_barem_discount_200_349: v})}
                className="data-[state=checked]:bg-blue-500"
              />
            </div>
          </div>
        </CardContent>
        <CardFooter className="bg-slate-950 px-6 py-4 flex justify-end">
          <Button 
            onClick={handleSaveSettings} 
            disabled={isSaving}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            {isSaving ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : <CheckCircle2 className="mr-2 h-4 w-4" />}
            Ayarları Kaydet
          </Button>
        </CardFooter>
      </Card>

      <Card className="bg-slate-900 border-slate-800/60 shadow-xl overflow-hidden relative">
        <div className="absolute top-0 left-0 w-1 h-full bg-emerald-500"></div>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-emerald-500/10 rounded-lg">
                <FileSpreadsheet className="h-5 w-5 text-emerald-400" />
              </div>
              <div>
                <CardTitle className="text-xl text-white">Özel Kargo Anlaşmanız</CardTitle>
                <CardDescription>Eğer kargo firmalarıyla doğrudan anlaşmanız varsa fiyatlarınızı Excel ile yükleyebilirsiniz.</CardDescription>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Switch 
                checked={settings.use_custom_cargo_rates}
                onCheckedChange={(v) => setSettings({...settings, use_custom_cargo_rates: v})}
                className="data-[state=checked]:bg-emerald-500"
              />
              <Label className="text-sm text-slate-300">Özel Fiyatları Kullan</Label>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="border border-dashed border-slate-700 rounded-xl p-6 flex flex-col items-center justify-center text-center space-y-3 bg-slate-950/30">
              <div className="p-3 bg-slate-800 rounded-full">
                <Download className="h-6 w-6 text-slate-300" />
              </div>
              <div>
                <h4 className="text-slate-200 font-medium">Şablonu İndir</h4>
                <p className="text-sm text-slate-400 mt-1">EcomMarj kargo fiyat şablonunu indirin ve Excel'de doldurun.</p>
              </div>
              <Button variant="outline" className="mt-2 border-slate-700 text-slate-300 hover:bg-slate-800" onClick={handleDownloadTemplate}>
                Şablonu İndir
              </Button>
            </div>

            <div className="border border-dashed border-emerald-500/30 rounded-xl p-6 flex flex-col items-center justify-center text-center space-y-3 bg-emerald-500/5 hover:bg-emerald-500/10 transition-colors">
              <div className="p-3 bg-emerald-500/20 rounded-full">
                <Upload className="h-6 w-6 text-emerald-400" />
              </div>
              <div>
                <h4 className="text-slate-200 font-medium">Fiyat Yükle</h4>
                <p className="text-sm text-slate-400 mt-1">Doldurduğunuz şablonu yükleyerek fiyatlarınızı güncelleyin.</p>
              </div>
              <div className="mt-2 relative">
                <input 
                  type="file" 
                  accept=".xlsx, .xls, .csv" 
                  onChange={handleFileUpload}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  disabled={isUploading}
                />
                <Button className="bg-emerald-600 hover:bg-emerald-700 text-white w-full pointer-events-none">
                  {isUploading ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : <Upload className="mr-2 h-4 w-4" />}
                  Excel Seç ve Yükle
                </Button>
              </div>
            </div>
          </div>

          {customRates.length > 0 && (
            <div className="mt-6 border border-slate-800 rounded-lg overflow-hidden">
              <div className="bg-slate-950 p-3 px-4 flex justify-between items-center border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-slate-300">Yüklü Fiyatlar</span>
                  <span className="px-2 py-0.5 rounded-full bg-slate-800 text-xs text-slate-400">{customRates.length} Desi Kaydı</span>
                </div>
                <Button variant="ghost" size="sm" className="h-8 text-red-400 hover:text-red-300 hover:bg-red-400/10" onClick={handleResetRates}>
                  <Trash2 className="h-3.5 w-3.5 mr-1" /> Sıfırla
                </Button>
              </div>
              <div className="max-h-64 overflow-y-auto custom-scrollbar bg-slate-900/50">
                <table className="w-full text-sm text-left text-slate-400">
                  <thead className="text-xs text-slate-400 uppercase bg-slate-900 sticky top-0">
                    <tr>
                      <th className="px-4 py-3 font-medium">Desi</th>
                      <th className="px-4 py-3 font-medium">Fiyat (KDV Dahil)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {customRates.map((r) => (
                      <tr key={r.id} className="hover:bg-slate-800/40">
                        <td className="px-4 py-2.5 font-medium text-slate-300">{r.desi} Desi</td>
                        <td className="px-4 py-2.5 text-emerald-400 font-medium">{r.price} TL</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {lastUploadDate && (
                <div className="p-2.5 bg-slate-950 text-xs text-slate-500 text-center border-t border-slate-800">
                  Son yükleme: {new Date(lastUploadDate).toLocaleString("tr-TR")}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
