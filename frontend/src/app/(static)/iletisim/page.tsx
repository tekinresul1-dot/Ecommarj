"use client";

import { useState } from "react";
import { Mail, Send } from "lucide-react";

export default function ContactPage() {
    const [submitted, setSubmitted] = useState(false);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setSubmitted(true);
    };

    return (
        <div className="pt-28 pb-20">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center mb-16">
                    <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4">
                        <span className="gradient-text">İletişim</span>
                    </h1>
                    <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                        Sorularınız veya önerileriniz için bize ulaşın. En kısa sürede yanıt vereceğiz.
                    </p>
                </div>

                <div className="grid gap-8 md:grid-cols-5">
                    {/* Contact Info */}
                    <div className="md:col-span-2 space-y-6">
                        <div className="glass-card rounded-2xl p-6">
                            <div className="w-10 h-10 rounded-lg bg-accent-500/10 border border-accent-500/20 flex items-center justify-center mb-4">
                                <Mail className="w-5 h-5 text-accent-400" />
                            </div>
                            <h3 className="text-white font-semibold mb-1">E-posta</h3>
                            <a href="mailto:destek@ecommarj.com" className="text-sm text-accent-400 hover:underline">
                                destek@ecommarj.com
                            </a>
                        </div>
                        <div className="glass-card rounded-2xl p-6">
                            <p className="text-sm text-slate-400 leading-relaxed">
                                İş günleri içinde genellikle 24 saat içinde yanıt veriyoruz.
                                Acil destek için konu satırına &ldquo;ACİL&rdquo; yazabilirsiniz.
                            </p>
                        </div>
                    </div>

                    {/* Contact Form */}
                    <div className="md:col-span-3">
                        <div className="glass-card rounded-2xl p-8">
                            {submitted ? (
                                <div className="text-center py-10">
                                    <div className="w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto mb-4">
                                        <Send className="w-7 h-7 text-emerald-400" />
                                    </div>
                                    <h3 className="text-xl font-semibold text-white mb-2">Mesajınız Alındı!</h3>
                                    <p className="text-slate-400">En kısa sürede size geri döneceğiz.</p>
                                </div>
                            ) : (
                                <form onSubmit={handleSubmit} className="space-y-5">
                                    <div className="grid gap-5 sm:grid-cols-2">
                                        <div>
                                            <label className="block text-sm font-medium text-slate-300 mb-1.5">Ad Soyad</label>
                                            <input
                                                type="text"
                                                required
                                                className="w-full bg-navy-950/50 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-accent-500/40 focus:border-accent-500/40 transition-all"
                                                placeholder="Adınız Soyadınız"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-slate-300 mb-1.5">E-posta</label>
                                            <input
                                                type="email"
                                                required
                                                className="w-full bg-navy-950/50 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-accent-500/40 focus:border-accent-500/40 transition-all"
                                                placeholder="ornek@email.com"
                                            />
                                        </div>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-300 mb-1.5">Konu</label>
                                        <input
                                            type="text"
                                            required
                                            className="w-full bg-navy-950/50 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-accent-500/40 focus:border-accent-500/40 transition-all"
                                            placeholder="Mesajınızın konusu"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-300 mb-1.5">Mesaj</label>
                                        <textarea
                                            required
                                            rows={5}
                                            className="w-full bg-navy-950/50 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-accent-500/40 focus:border-accent-500/40 transition-all resize-none"
                                            placeholder="Mesajınızı buraya yazın..."
                                        />
                                    </div>
                                    <button
                                        type="submit"
                                        className="w-full bg-gradient-to-r from-accent-500 to-electric-500 text-white py-3 rounded-xl font-medium hover:opacity-90 transition-opacity shadow-lg shadow-accent-500/20 flex items-center justify-center gap-2"
                                    >
                                        <Send className="w-4 h-4" /> Gönder
                                    </button>
                                </form>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
