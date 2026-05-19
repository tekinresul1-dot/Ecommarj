import Link from "next/link";

type GoogleCallbackPageProps = {
    searchParams?: Promise<{
        error?: string;
        error_description?: string;
    }>;
};

export default async function GoogleCallbackPage({ searchParams }: GoogleCallbackPageProps) {
    const params = await searchParams;
    const hasError = Boolean(params?.error);
    const description = params?.error_description || params?.error;

    return (
        <div className="w-full max-w-md">
            <div className="glass-card rounded-2xl border border-white/10 p-8 sm:p-10 shadow-2xl shadow-black/20">
                <div className="text-center">
                    <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl border border-white/10 bg-white/5 shadow-inner shadow-white/5">
                        <span className="text-2xl font-bold text-white">G</span>
                    </div>
                    <h1 className="text-3xl font-semibold text-white tracking-tight">
                        {hasError ? "Google Girişi Tamamlanamadı" : "Google Girişine Devam Et"}
                    </h1>
                    <p className="mt-3 text-sm md:text-base text-white/60 leading-relaxed">
                        {hasError
                            ? "Google hesabınızdan dönüş sırasında bir sorun oluştu."
                            : "Google ile giriş işlemini güvenli giriş ekranında tamamlayabilirsiniz."}
                    </p>
                </div>

                {description && (
                    <div className="mt-6 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3 text-sm text-rose-300">
                        {description}
                    </div>
                )}

                <div className="mt-6 grid gap-3 sm:grid-cols-2">
                    <Link
                        href="/google-giris"
                        className="h-11 rounded-xl bg-gradient-to-r from-accent-500 to-electric-500 hover:from-accent-400 hover:to-electric-400 text-white font-semibold transition-all flex items-center justify-center"
                    >
                        Google Girişine Dön
                    </Link>
                    <Link
                        href="/giris"
                        className="h-11 rounded-xl border border-white/10 bg-white/5 hover:bg-white/8 text-white/80 hover:text-white transition-all flex items-center justify-center"
                    >
                        Diğer Girişler
                    </Link>
                </div>
            </div>
        </div>
    );
}
