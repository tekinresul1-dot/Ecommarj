"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { AlertCircle, Key, User, Shield, CheckCircle2, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import { toast } from "sonner";

export default function SettingsPage() {
  const [apiKey, setApiKey] = useState("");
  const [apiSecret, setApiSecret] = useState("");
  const [sellerId, setSellerId] = useState("");

  const [isPageLoading, setIsPageLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);

  // Load existing credentials on mount
  useEffect(() => {
    let isMounted = true;
    const fetchCredentials = async () => {
      try {
        const response: any = await api.get("/integrations/trendyol/save-credentials/");
        if (isMounted && response) {
          setApiKey(response.api_key || "");
          setApiSecret(response.api_secret || "");
          setSellerId(response.supplier_id || "");
        }
      } catch (error: any) {
        console.error("Failed to fetch settings:", error);
        toast.error("Ayarlar yüklenirken bir sorun oluştu", {
          description: error.message || "Lütfen sayfayı yenilemeyi deneyin.",
        });
      } finally {
        if (isMounted) {
          setIsPageLoading(false);
        }
      }
    };

    fetchCredentials();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleTestConnection = async () => {
    if (!sellerId.trim() || !apiKey.trim() || !apiSecret.trim()) {
      toast.error("Eksik Bilgi", {
        description: "Test yapmadan önce Satıcı ID, API Key ve API Secret girdiğinizden emin olun."
      });
      return false;
    }

    setIsTesting(true);
    let success = false;
    try {
      const result: any = await api.post("/integrations/trendyol/test-connection/", {
        api_key: apiKey,
        api_secret: apiSecret,
        supplier_id: sellerId
      });

      if (result.ok) {
        toast.success("Bağlantı Başarılı!", {
          description: `Trendyol API'ye bağlanıldı. ${result.sample_product_count_hint} ürün bulundu.`
        });
        success = true;
      } else {
        toast.error("Bağlantı Başarısız", {
          description: result.message || "Trendyol API'ye bağlanılamadı."
        });
      }
    } catch (error: any) {
      console.error("Test connection error:", error);
      toast.error("Bağlantı Hatası", {
        description: error.message || "API test edilirken sunucu hatası oluştu."
      });
    } finally {
      setIsTesting(false);
    }
    return success;
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!sellerId.trim()) {
      toast.error("Eksik Bilgi", { description: "Lütfen Trendyol Satıcı ID bilginizi girin." });
      return;
    }

    setIsSaving(true);

    try {
      // Step 1: Enforce API Connection Test if tokens are provided
      if (apiKey || apiSecret) {
        toast.loading("Bağlantı test ediliyor...", { id: "save-toast" });
        const isConnectionOk = await handleTestConnection();
        if (!isConnectionOk) {
          toast.dismiss("save-toast");
          setIsSaving(false);
          return; // Durdur, test başarısızsa kaydetme
        }
        toast.loading("Bilgiler şifrelenip kaydediliyor...", { id: "save-toast" });
      } else {
        toast.loading("Ayarlar güncelleniyor...", { id: "save-toast" });
      }

      // Step 2: Save to DB securely
      const saveResponse: any = await api.post("/integrations/trendyol/save-credentials/", {
        api_key: apiKey,
        api_secret: apiSecret,
        supplier_id: sellerId,
        auto_sync: true
      });

      toast.success("Ayarlar Kaydedildi", {
        id: "save-toast",
        description: saveResponse.message || "Bilgileriniz güvenli bir şekilde sunucuda saklandı."
      });

    } catch (error: any) {
      console.error("Save credentials error:", error);
      toast.error("Kayıt Başarısız", {
        id: "save-toast",
        description: error.message || "Ayarlar veritabanına kaydedilirken hata oluştu."
      });
    } finally {
      setIsSaving(false);
    }
  };

  if (isPageLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-emerald-500 border-t-transparent shadow-lg"></div>
        <p className="text-slate-400 font-medium animate-pulse">Entegrasyon bilgileri yükleniyor...</p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto py-8 px-4 sm:px-6 lg:px-8 animate-in fade-in duration-500">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Ayarlar & Entegrasyonlar</h1>
        <p className="text-slate-400">Pazaryeri API bağlantılarınızı buradan güvenle yönetebilirsiniz.</p>
      </div>

      <Card className="bg-slate-900 border-slate-800/60 shadow-2xl overflow-hidden relative backdrop-blur-sm">
        <div className="absolute top-0 left-0 w-1.5 h-full bg-gradient-to-b from-orange-400 to-orange-600"></div>

        <CardHeader className="pb-6 border-b border-white/5 bg-white/[0.02]">
          <div className="flex items-center gap-4">
            <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-orange-500/10 border border-orange-500/20 shadow-inner">
              <span className="text-orange-500 font-bold text-xl ml-1">t.</span>
            </div>
            <div>
              <CardTitle className="text-xl text-white font-semibold flex items-center gap-2">
                Trendyol API Bağlantısı
              </CardTitle>
              <CardDescription className="text-slate-400 mt-1">
                Kâr/Zarar analizi için Satıcı Paneli &gt; Entegrasyon Bilgileri sayfasındaki API kodlarını girin.
              </CardDescription>
            </div>
          </div>
        </CardHeader>

        <form onSubmit={handleSave} autoComplete="off">
          <CardContent className="space-y-6 pt-6 pb-2">

            <div className="grid gap-6 sm:grid-cols-1">
              <div className="space-y-2.5">
                <Label htmlFor="sellerId" className="text-slate-200 font-medium">Satıcı ID (Supplier ID) <span className="text-red-400">*</span></Label>
                <div className="relative group">
                  <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-slate-500 group-focus-within:text-orange-500 transition-colors">
                    <User size={18} />
                  </div>
                  <Input
                    id="sellerId"
                    value={sellerId}
                    onChange={(e) => setSellerId(e.target.value)}
                    placeholder="Örn: 123456"
                    className="pl-10 h-11 bg-slate-950/50 border-slate-700 focus-visible:ring-orange-500 focus-visible:border-orange-500 text-slate-100 transition-all placeholder:text-slate-600"
                    autoComplete="off"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2.5">
                <Label htmlFor="apiKey" className="text-slate-200 font-medium">Trendyol API Key</Label>
                <div className="relative group">
                  <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-slate-500 group-focus-within:text-orange-500 transition-colors">
                    <Key size={18} />
                  </div>
                  <Input
                    id="apiKey"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="K89KKC..."
                    className="pl-10 h-11 bg-slate-950/50 border-slate-700 focus-visible:ring-orange-500 focus-visible:border-orange-500 text-slate-100 font-mono text-sm transition-all placeholder:text-slate-600"
                    autoComplete="off"
                  />
                </div>
              </div>

              <div className="space-y-2.5">
                <Label htmlFor="apiSecret" className="text-slate-200 font-medium">Trendyol API Secret</Label>
                <div className="relative group">
                  <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-slate-500 group-focus-within:text-orange-500 transition-colors">
                    <Shield size={18} />
                  </div>
                  <Input
                    id="apiSecret"
                    type="password"
                    value={apiSecret}
                    onChange={(e) => setApiSecret(e.target.value)}
                    placeholder="••••••••••••••••"
                    className="pl-10 h-11 bg-slate-950/50 border-slate-700 focus-visible:ring-orange-500 focus-visible:border-orange-500 text-slate-100 font-mono text-lg tracking-widest transition-all placeholder:text-slate-600 placeholder:tracking-normal placeholder:text-base"
                    autoComplete="new-password"
                  />
                </div>
              </div>
            </div>

            <div className="rounded-xl bg-orange-500/10 border border-orange-500/20 p-4 mt-8 flex items-start gap-3">
              <AlertCircle className="text-orange-500 shrink-0 mt-0.5" size={20} />
              <div className="space-y-1">
                <h4 className="font-medium text-orange-200">Veri Güvenliği ve Senkronizasyon</h4>
                <p className="text-sm text-slate-400 leading-relaxed">
                  Güvenliğiniz için API Secret şifrelenerek saklanmaktadır. Bilgilerinizi kaydettiğinizde EcomPro arka planda ürünlerinizi, komisyonları ve satış verilerinizi otomatik çekmeye başlar.
                </p>
              </div>
            </div>

          </CardContent>

          <CardFooter className="bg-slate-950 border-t border-slate-800/80 px-6 py-4 flex flex-col sm:flex-row gap-3 justify-end items-center">
            <Button
              type="button"
              variant="outline"
              onClick={handleTestConnection}
              disabled={isTesting || isSaving || !sellerId || !apiKey || !apiSecret}
              className="w-full sm:w-auto border-slate-700 hover:bg-slate-800 text-slate-300 transition-colors h-11 px-6 rounded-lg font-medium"
            >
              {isTesting ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin text-orange-500" /> Test Ediliyor...
                </>
              ) : (
                "Bağlantıyı Test Et"
              )}
            </Button>

            <Button
              type="submit"
              disabled={isSaving || isTesting}
              className="w-full sm:w-auto bg-orange-500 hover:bg-orange-600 text-white shadow-lg shadow-orange-500/20 transition-all h-11 px-8 rounded-lg font-medium"
            >
              {isSaving ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Kaydediliyor...
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4 mr-2" /> Ayarları Kaydet
                </>
              )}
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}