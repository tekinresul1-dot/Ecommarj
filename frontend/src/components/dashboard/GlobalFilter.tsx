"use client";

import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { useCallback, useState, useEffect, useRef } from "react";
import clsx from "clsx";
import { Calendar as CalendarIcon, Globe, ChevronDown, Check } from "lucide-react";
import { DateRange } from "react-day-picker";
import { format, parseISO } from "date-fns";
import { DatePickerWithRange } from "./DateRangePicker";

const MICRO_COUNTRIES = [
    { code: "TR", name: "Türkiye" },
    { code: "SA", name: "Suudi Arabistan" },
    { code: "AE", name: "Birleşik Arap Emirlikleri" },
    { code: "QA", name: "Katar" },
    { code: "KW", name: "Kuveyt" },
    { code: "OM", name: "Umman" },
    { code: "BH", name: "Bahreyn" },
    { code: "AZ", name: "Azerbaycan" },
    { code: "RO", name: "Romanya" },
    { code: "GR", name: "Yunanistan" },
    { code: "BG", name: "Bulgaristan" },
    { code: "UA", name: "Ukrayna" },
    { code: "MD", name: "Moldova" },
];

export function GlobalFilter() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const pathname = usePathname();

    const channel = searchParams.get("channel") || "trendyol";

    const [countries, setCountries] = useState<string[]>([]);
    const [countryDropdownOpen, setCountryDropdownOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    // Tarih seçimi state'i
    const [dateRange, setDateRange] = useState<DateRange | undefined>(undefined);

    useEffect(() => {
        const c = searchParams.get("countries");
        setCountries(c ? c.split(",") : []);

        // URL'den min_date / max_date okuma
        const min_date = searchParams.get("min_date");
        const max_date = searchParams.get("max_date");
        if (min_date && max_date) {
            setDateRange({
                from: parseISO(min_date),
                to: parseISO(max_date),
            });
        }
    }, [searchParams]);

    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setCountryDropdownOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

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
        let newC = [...countries];
        if (code === "ALL") {
            newC = newC.length === MICRO_COUNTRIES.length ? [] : MICRO_COUNTRIES.map(c => c.code);
        } else {
            newC = newC.includes(code) ? newC.filter(c => c !== code) : [...newC, code];
        }
        setCountries(newC);
    };

    const applyCountryFilter = () => {
        setCountryDropdownOpen(false);
        router.push(pathname + "?" + createQueryString("countries", countries.join(",")));
    };

    const handleDateChange = (newDateRange: DateRange | undefined) => {
        setDateRange(newDateRange);
        if (newDateRange?.from && newDateRange?.to) {
            const min_date = format(newDateRange.from, "yyyy-MM-dd");
            const max_date = format(newDateRange.to, "yyyy-MM-dd");

            const params = new URLSearchParams(searchParams.toString());
            params.set("min_date", min_date);
            params.set("max_date", max_date);
            router.push(pathname + "?" + params.toString());
        }
    };

    const isAllSelected = countries.length === MICRO_COUNTRIES.length && MICRO_COUNTRIES.length > 0;

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

            <div className="flex flex-wrap gap-4 items-center w-full xl:w-auto justify-end">
                {channel === "micro_export" && (
                    <div className="relative" ref={dropdownRef}>
                        <button
                            onClick={() => setCountryDropdownOpen(!countryDropdownOpen)}
                            className={clsx(
                                "flex items-center gap-3 bg-navy-950 border rounded-xl px-4 py-1.5 h-11 w-full sm:w-auto transition-colors",
                                countryDropdownOpen ? "border-purple-500/50 text-white" : "border-white/10 text-white/70 hover:text-white hover:border-white/20"
                            )}
                        >
                            <Globe className="w-4 h-4 text-purple-400" />
                            <span className="text-sm font-medium">
                                {countries.length === 0 ? "Ülke Seçin" : countries.length === MICRO_COUNTRIES.length ? "Tüm Ülkeler" : `${countries.length} Ülke Seçili`}
                            </span>
                            <ChevronDown className={clsx("w-4 h-4 transition-transform", countryDropdownOpen && "rotate-180")} />
                        </button>

                        {countryDropdownOpen && (
                            <div className="absolute right-0 top-full mt-2 w-72 bg-navy-900 border border-white/10 rounded-xl shadow-2xl z-50 overflow-hidden flex flex-col max-h-[400px]">
                                <div className="p-3 border-b border-white/10 bg-navy-950/50">
                                    <label className="flex items-center gap-3 cursor-pointer group">
                                        <div className={clsx("w-5 h-5 rounded border flex items-center justify-center transition-colors", isAllSelected ? "bg-purple-600 border-purple-500" : "border-white/20 bg-navy-950 group-hover:border-white/40")}>
                                            {isAllSelected && <Check className="w-3.5 h-3.5 text-white" />}
                                        </div>
                                        <span className="text-sm font-medium text-white">Tümünü Seç</span>
                                        <input type="checkbox" className="hidden" checked={isAllSelected} onChange={() => toggleCountry("ALL")} />
                                    </label>
                                </div>

                                <div className="overflow-y-auto flex-1 p-2 scrollbar-thin scrollbar-thumb-white/10">
                                    {MICRO_COUNTRIES.map((c) => {
                                        const isSelected = countries.includes(c.code);
                                        return (
                                            <label key={c.code} className="flex items-center justify-between p-2 rounded-lg hover:bg-white/5 cursor-pointer group transition-colors">
                                                <div className="flex items-center gap-3">
                                                    <div className={clsx("w-5 h-5 rounded border flex items-center justify-center transition-colors", isSelected ? "bg-purple-600 border-purple-500" : "border-white/20 bg-navy-950 group-hover:border-white/40")}>
                                                        {isSelected && <Check className="w-3.5 h-3.5 text-white" />}
                                                    </div>
                                                    <span className={clsx("text-sm transition-colors", isSelected ? "text-white font-medium" : "text-white/70 group-hover:text-white")}>{c.name}</span>
                                                </div>
                                                <span className={`fi fi-${c.code.toLowerCase()} rounded-[2px] shadow-sm text-lg w-6 shrink-0`}></span>
                                                <input type="checkbox" className="hidden" checked={isSelected} onChange={() => toggleCountry(c.code)} />
                                            </label>
                                        );
                                    })}
                                </div>

                                <div className="p-3 border-t border-white/10 bg-navy-950/80 mt-auto">
                                    <button
                                        onClick={applyCountryFilter}
                                        className="w-full bg-purple-600 hover:bg-purple-500 text-white text-sm font-semibold py-2.5 rounded-lg transition-colors"
                                    >
                                        Filtrele
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                )}
                <DatePickerWithRange
                    date={dateRange}
                    setDate={handleDateChange}
                />
            </div>
        </div>
    )
}
