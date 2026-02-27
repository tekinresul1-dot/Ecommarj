"use client";

import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { useCallback, useState, useEffect } from "react";
import clsx from "clsx";
import { Calendar, Globe } from "lucide-react";

export function GlobalFilter() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const pathname = usePathname();

    const channel = searchParams.get("channel") || "trendyol";

    const [countries, setCountries] = useState<string[]>([]);

    useEffect(() => {
        const c = searchParams.get("countries");
        setCountries(c ? c.split(",") : []);
    }, [searchParams]);

    const createQueryString = useCallback(
        (name: string, value: string) => {
            const params = new URLSearchParams(searchParams.toString());
            if (value) {
                params.set(name, value);
            } else {
                params.delete(name);
            }
            return params.toString();
        },
        [searchParams]
    );

    const handleChannelSwitch = (newChannel: string) => {
        let qs = createQueryString("channel", newChannel);
        if (newChannel === "trendyol") {
            const params = new URLSearchParams(qs);
            params.delete("countries");
            qs = params.toString();
        }
        router.push(pathname + "?" + qs);
    };

    const toggleCountry = (code: string) => {
        const newC = countries.includes(code) ? countries.filter(c => c !== code) : [...countries, code];
        router.push(pathname + "?" + createQueryString("countries", newC.join(",")));
    };

    return (
        <div className="bg-navy-900 border border-white/10 rounded-2xl p-4 mb-6 flex flex-col xl:flex-row items-start xl:items-center gap-4 justify-between shadow-lg">
            <div className="flex bg-navy-950 rounded-xl p-1 border border-white/5 shadow-inner w-full sm:w-auto">
                <button
                    onClick={() => handleChannelSwitch("trendyol")}
                    className={clsx(
                        "px-6 py-2.5 rounded-lg text-sm font-semibold transition-all duration-300 flex-1 sm:flex-none",
                        channel === "trendyol"
                            ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-[0_0_15px_rgba(59,130,246,0.3)] ring-1 ring-white/10"
                            : "text-white/60 hover:text-white hover:bg-white/5"
                    )}
                >
                    Trendyol
                </button>
                <button
                    onClick={() => handleChannelSwitch("micro_export")}
                    className={clsx(
                        "px-6 py-2.5 rounded-lg text-sm font-semibold transition-all duration-300 flex-1 sm:flex-none",
                        channel === "micro_export"
                            ? "bg-gradient-to-r from-violet-600 to-purple-600 text-white shadow-[0_0_15px_rgba(139,92,246,0.3)] ring-1 ring-white/10"
                            : "text-white/60 hover:text-white hover:bg-white/5"
                    )}
                >
                    Mikro İhracat
                </button>
            </div>

            <div className="flex flex-wrap gap-4 items-center w-full xl:w-auto">
                {channel === "micro_export" && (
                    <div className="flex items-center gap-3 bg-navy-950 border border-white/10 rounded-xl px-4 py-1.5 h-11 w-full sm:w-auto">
                        <Globe className="w-4 h-4 text-white/40" />
                        <div className="flex gap-4 items-center overflow-x-auto scrollbar-hide py-1">
                            {["AZ", "AE", "SA", "RO", "BG"].map(code => (
                                <label key={code} className="flex items-center gap-2 cursor-pointer text-sm font-medium text-white/80 hover:text-white whitespace-nowrap">
                                    <input
                                        type="checkbox"
                                        className="rounded border-white/20 bg-navy-900 text-purple-500 focus:ring-purple-500/50 h-4 w-4 transition-colors cursor-pointer"
                                        checked={countries.includes(code)}
                                        onChange={() => toggleCountry(code)}
                                    />
                                    {code}
                                </label>
                            ))}
                        </div>
                    </div>
                )}
                <div className="flex items-center gap-3 bg-navy-950 border border-white/10 rounded-xl px-4 h-11 w-full sm:w-auto">
                    <Calendar className="w-4 h-4 text-white/40" />
                    <select className="bg-transparent text-white font-medium text-sm outline-none focus:ring-0 cursor-pointer appearance-none pr-8 w-full h-full">
                        <option value="today" className="bg-navy-900">Bugün</option>
                        <option value="7days" className="bg-navy-900">Son 7 Gün</option>
                        <option value="30days" className="bg-navy-900">Son 30 Gün</option>
                        <option value="this_month" className="bg-navy-900">Bu Ay</option>
                        <option value="last_month" className="bg-navy-900">Geçen Ay</option>
                        <option value="all_time" className="bg-navy-900">Tüm Zamanlar</option>
                    </select>
                </div>
            </div>
        </div>
    )
}
