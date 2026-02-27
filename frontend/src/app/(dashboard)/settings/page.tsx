"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { AlertCircle, Key, User, Shield, CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";
import { toast } from "sonner";

export default function SettingsPage() {
  const [apiKey, setApiKey] = useState("");
  const [apiSecret, setApiSecret] = useState("");
  const [sellerId, setSellerId] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isFetching, setIsFetching] = useState(true);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const data = await api.get("/settings/trendyol/");
        if (data) {
          setApiKey(data.api_key || "");
          setApiSecret(data.api_secret || "");
          setSellerId(data.seller_id || "");
        }
      } catch (error) {
        console.error("Settings fetch error:", error);
        toast.error("Ayarlar yüklenirken bir sorun oluştu.");
      } finally {
        setIsFetching(false);
      }
    };

    fetchSettings();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!sellerId.trim()) {
      toast.error("Satıcı ID girmek zorunludur.");
      return;
    }

    setIsLoading(true);

    try {
      const response = await api.post("/settings/trendyol/", {
        api_key: apiKey,
        api_secret: apiSecret,
        seller_id: sellerId,
        auto_sync: true // İstendiği gibi direkt sync triggerla
      });

      toast.success("Trendyol API Bilgileri kaydedildi", {
        description: "Sipariş ve Ürün senkronizasyonu arka planda başlatıldı."
      });
    } catch (error: any) {
      console.error("Save error:", error);
      toast.error(error.message || "Ayarlar kaydedilemedi. Lütfen tekrar deneyin.");
    } finally {
      setIsLoading(false);
    }
  };

  if (isFetching) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-500 border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-2xl mx-auto py-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white mb-2">Entegrasyon Ayarları</h1>
        <p className="text-slate-400">Pazaryeri API bağlantılarınızı buradan yönetebilirsiniz.</p>
      </div>

      <Card className="bg-slate-900 border-slate-800 shadow-xl overflow-hidden relative">
        <div className="absolute top-0 left-0 w-1 h-full bg-emerald-500"></div>
        <CardHeader>
          <CardTitle className="text-xl text-white flex items-center gap-2">
            <div className="bg-orange-500/10 p-2 rounded-lg">
              <img src="https://cdn.dsmcdn.com/web/logo/trendyol-log-v2.svg" alt="Trendyol" className="h-4 brightness-200" />
            </div>
            Trendyol API Bilgileri
          </CardTitle>
          <CardDescription className="text-slate-400">
            Kâr/Zarar hesaplamaları ve otomatik entegrasyon için Trendyol Satıcı Paneli'nden aldığınız bilgileri giriniz.
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleSave}>
          <CardContent className="space-y-6">

            <div className="space-y-2">
              <Label htmlFor="sellerId" className="text-slate-200">Trendyol Satıcı ID <span className="text-red-500">*</span></Label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-slate-500">
                  <User size={16} />
                </div>
                <Input
                  id="sellerId"
                  value={sellerId}
                  onChange={(e) => setSellerId(e.target.value)}
                  placeholder="Örn: 123456"
                  className="pl-10 bg-slate-950 border-slate-800 focus-visible:ring-emerald-500 text-slate-200"
                  required
                />
              </div>
              <p className="text-xs text-slate-500">Satıcı panelinizde sağ üst kısımdaki isminize tıklayarak görebilirsiniz.</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="apiKey" className="text-slate-200">Trendyol API Key</Label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-slate-500">
                  <Key size={16} />
                </div>
                <Input
                  id="apiKey"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="K89KKC..."
                  className="pl-10 bg-slate-950 border-slate-800 focus-visible:ring-emerald-500 text-slate-200 font-mono"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="apiSecret" className="text-slate-200">Trendyol API Secret</Label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-slate-500">
                  <Shield size={16} />
                </div>
                <Input
                  id="apiSecret"
                  type="password"
                  value={apiSecret}
                  onChange={(e) => setApiSecret(e.target.value)}
                  placeholder="••••••••••••••••"
                  className="pl-10 bg-slate-950 border-slate-800 focus-visible:ring-emerald-500 text-slate-200 font-mono"
                />
              </div>
            </div>

            <div className="rounded-lg bg-emerald-500/10 border border-emerald-500/20 p-4 mt-6">
              <div className="flex gap-3">
                <AlertCircle className="text-emerald-500 shrink-0" size={20} />
                <div className="space-y-1">
                  <h4 className="font-medium text-emerald-500">Otomatik Senkronizasyon</h4>
                  <p className="text-sm text-slate-400">
                    Bilgilerinizi kaydettiğiniz anda "Veri Çekme Motoru" arkaplanda otomatik olarak tetiklenerek sipariş, KDV, komisyon ve liste fiyatlarınızı EcomPro'ya aktaracaktır.
                  </p>
                </div>
              </div>
            </div>

          </CardContent>
          <CardFooter className="bg-slate-950/50 border-t border-slate-800 justify-end py-4">
            <Button
              type="submit"
              disabled={isLoading}
              className="bg-orange-500 hover:bg-orange-600 text-white min-w-[120px]"
            >
              {isLoading ? (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent mr-2"></div>
              ) : (
                <CheckCircle2 className="w-4 h-4 mr-2" />
              )}
              {isLoading ? "Kaydediliyor..." : "Kaydet"}
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}