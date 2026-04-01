"use client"

import * as React from "react"
import { format, subDays, startOfMonth, startOfToday, endOfMonth, endOfToday, subMonths } from "date-fns"
import { tr } from "date-fns/locale"
import { Calendar as CalendarIcon } from "lucide-react"
import { DateRange } from "react-day-picker"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"

interface DatePickerWithRangeProps extends React.HTMLAttributes<HTMLDivElement> {
    date: DateRange | undefined;
    setDate: (date: DateRange | undefined) => void;
}

const PRESETS = [
    { label: "Bugün",     getValue: () => ({ from: startOfToday(), to: endOfToday() }) },
    { label: "Dün",       getValue: () => ({ from: subDays(startOfToday(), 1), to: subDays(startOfToday(), 1) }) },
    { label: "Son 7 Gün", getValue: () => ({ from: subDays(startOfToday(), 7), to: endOfToday() }) },
    { label: "Son 30 Gün",getValue: () => ({ from: subDays(startOfToday(), 30), to: endOfToday() }) },
    { label: "Bu Ay",     getValue: () => ({ from: startOfMonth(startOfToday()), to: endOfMonth(startOfToday()) }) },
    { label: "Geçen Ay",  getValue: () => {
        const s = startOfMonth(subMonths(startOfToday(), 1));
        const e = endOfMonth(subMonths(startOfToday(), 1));
        return { from: s, to: e };
    }},
];

export function DatePickerWithRange({ className, date, setDate }: DatePickerWithRangeProps) {
    const [isOpen, setIsOpen]           = React.useState(false);
    // 'from' = waiting for 1st click, 'to' = waiting for 2nd click
    const [phase, setPhase]             = React.useState<'from' | 'to'>('from');
    const [tempFrom, setTempFrom]       = React.useState<Date | undefined>(date?.from);
    const [tempTo, setTempTo]           = React.useState<Date | undefined>(date?.to);
    const [activePreset, setActivePreset] = React.useState<string | null>(null);

    // Sync when popover opens; always reset to 'from' phase
    React.useEffect(() => {
        if (isOpen) {
            setTempFrom(date?.from);
            setTempTo(date?.to);
            setActivePreset(null);
            setPhase('from');
        }
    }, [isOpen]); // eslint-disable-line react-hooks/exhaustive-deps

    // Preset: apply immediately, close popover — no "Uygula" needed
    const handlePreset = (preset: typeof PRESETS[0]) => {
        const value = preset.getValue();
        setDate(value);
        setActivePreset(preset.label);
        setIsOpen(false);
    };

    // Two-click range selection — fully controlled, react-day-picker won't interfere
    const handleDayClick = (day: Date | undefined) => {
        if (!day) return;
        setActivePreset(null);

        if (phase === 'from') {
            // 1st click → set start, wait for end
            setTempFrom(day);
            setTempTo(undefined);
            setPhase('to');
        } else {
            // 2nd click → complete range
            if (!tempFrom) {
                setTempFrom(day);
                return;
            }
            if (day >= tempFrom) {
                setTempTo(day);
            } else {
                // Clicked before start → swap
                setTempTo(tempFrom);
                setTempFrom(day);
            }
            // Stay in 'to' — range complete, await Uygula
        }
    };

    const handleApply = () => {
        if (tempFrom && tempTo) {
            setDate({ from: tempFrom, to: tempTo });
        }
        setIsOpen(false);
    };

    // Modifiers passed to Calendar so range_start/middle/end styling works
    const rangeModifiers = React.useMemo(() => ({
        range_start:  tempFrom ? [tempFrom] : [],
        range_end:    tempTo   ? [tempTo]   : [],
        range_middle: tempFrom && tempTo
            ? { after: tempFrom, before: tempTo }
            : [],
    }), [tempFrom, tempTo]);

    return (
        <div className={cn("grid gap-2", className)}>
            <Popover open={isOpen} onOpenChange={setIsOpen}>
                <PopoverTrigger asChild>
                    <Button
                        id="date"
                        variant={"outline"}
                        className={cn(
                            "w-full sm:w-[280px] justify-start text-left font-normal bg-navy-950/80 border-white/10 backdrop-blur-sm text-white/90 data-[state=open]:bg-white/5 data-[state=open]:border-blue-500/50 hover:bg-white/10 hover:text-white hover:border-white/20 h-10 transition-all duration-200",
                            !date && "text-white/50"
                        )}
                    >
                        <CalendarIcon className="mr-2 h-4 w-4 text-blue-400" />
                        {date?.from ? (
                            date.to ? (
                                <>
                                    {format(date.from, "dd MMM yyyy", { locale: tr })} –{" "}
                                    {format(date.to,   "dd MMM yyyy", { locale: tr })}
                                </>
                            ) : (
                                format(date.from, "dd MMM yyyy", { locale: tr })
                            )
                        ) : (
                            <span>Tarih Aralığı Seçin</span>
                        )}
                    </Button>
                </PopoverTrigger>

                <PopoverContent
                    className="w-auto p-0 bg-navy-950 border-white/10 text-white shadow-2xl rounded-xl overflow-hidden animate-in zoom-in-95 duration-200"
                    align="end"
                >
                    <div className="flex flex-col sm:flex-row">

                        {/* ── Presets (direkt uygular) ── */}
                        <div className="flex sm:flex-col p-3 border-b sm:border-b-0 sm:border-r border-white/10 bg-black/20 min-w-[140px] gap-1.5 overflow-x-auto sm:overflow-visible">
                            <div className="text-[11px] font-semibold text-white/40 uppercase tracking-widest mb-2 px-2 hidden sm:block">
                                Hızlı Seçim
                            </div>
                            {PRESETS.map((preset) => (
                                <button
                                    key={preset.label}
                                    onClick={() => handlePreset(preset)}
                                    className={cn(
                                        "px-3 py-2 text-[13px] text-left rounded-lg transition-all font-medium whitespace-nowrap sm:whitespace-normal",
                                        activePreset === preset.label
                                            ? "bg-blue-600/20 text-blue-400 ring-1 ring-blue-500/30"
                                            : "text-white/70 hover:bg-white/10 hover:text-white"
                                    )}
                                >
                                    {preset.label}
                                </button>
                            ))}
                        </div>

                        {/* ── Calendar (mode="single" + custom range modifiers) ── */}
                        <div className="p-4 bg-navy-950">
                            <Calendar
                                initialFocus
                                mode="single"
                                selected={undefined}
                                onSelect={handleDayClick}
                                defaultMonth={tempFrom}
                                modifiers={rangeModifiers}
                                numberOfMonths={2}
                                locale={tr}
                                className="bg-transparent text-white"
                            />

                            {/* ── Footer ── */}
                            <div className="flex items-center justify-between pt-4 border-t border-white/10 mt-4 gap-3">
                                {/* Selected range display */}
                                <div className="text-[13px] font-medium bg-black/20 px-3 py-1.5 rounded-md border border-white/5 min-w-[210px]">
                                    {tempFrom ? (
                                        tempTo ? (
                                            <>
                                                <span className="text-white/80">{format(tempFrom, "dd MMM yyyy", { locale: tr })}</span>
                                                <span className="mx-2 text-white/30">→</span>
                                                <span className="text-white/80">{format(tempTo, "dd MMM yyyy", { locale: tr })}</span>
                                            </>
                                        ) : (
                                            <>
                                                <span className="text-white/80">{format(tempFrom, "dd MMM yyyy", { locale: tr })}</span>
                                                <span className="mx-2 text-blue-400/70 animate-pulse">→ bitiş seçin</span>
                                            </>
                                        )
                                    ) : (
                                        <span className="text-white/40">Başlangıç tarihi seçin</span>
                                    )}
                                </div>

                                {/* Actions */}
                                <div className="flex gap-2">
                                    <Button
                                        size="sm"
                                        variant="ghost"
                                        className="text-[13px] text-white/70 hover:text-white hover:bg-white/10 h-8 px-4 rounded-md"
                                        onClick={() => setIsOpen(false)}
                                    >
                                        İptal
                                    </Button>
                                    <Button
                                        size="sm"
                                        disabled={!tempFrom || !tempTo}
                                        className="h-8 px-5 text-[13px] font-medium bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white border-0 rounded-md transition-all"
                                        onClick={handleApply}
                                    >
                                        Uygula
                                    </Button>
                                </div>
                            </div>
                        </div>
                    </div>
                </PopoverContent>
            </Popover>
        </div>
    );
}
