import Link from "next/link";

export default function AuthLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="relative min-h-screen flex flex-col bg-navy-950">
            {/* Background effects — same as landing */}
            <div className="fixed inset-0 pointer-events-none z-0">
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-accent-500/10 rounded-full blur-[160px]" />
                <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-electric-500/8 rounded-full blur-[100px]" />
                <div className="absolute inset-0 bg-[linear-gradient(rgba(56,189,248,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(56,189,248,0.03)_1px,transparent_1px)] bg-[size:60px_60px]" />
            </div>

            {/* Minimal navbar */}
            <nav className="relative z-10 h-16 flex items-center border-b border-white/5 bg-navy-950/80 backdrop-blur-xl">
                <div className="w-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
                    <Link href="/" className="flex items-center gap-2.5 group shrink-0">
                        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-accent-400 to-electric-500 flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-accent-500/25">
                            E
                        </div>
                        <span className="text-xl font-bold text-white tracking-tight">
                            Ecom<span className="gradient-text-blue">Pro</span>
                        </span>
                    </Link>

                    <div className="flex items-center gap-3">
                        <Link
                            href="/"
                            className="text-sm text-slate-400 hover:text-white transition-colors px-3 py-2"
                        >
                            Ana Sayfa
                        </Link>
                    </div>
                </div>
            </nav>

            {/* Page content */}
            <main className="relative z-10 flex-1 flex items-center justify-center py-12 sm:py-16 lg:py-20 px-4 sm:px-6">
                {children}
            </main>
        </div>
    );
}
