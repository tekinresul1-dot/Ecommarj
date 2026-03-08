"use client"

import * as React from "react"
import { addDays, format, subDays, startOfMonth, startOfToday, endOfMonth, endOfToday, subMonths } from "date-fns"
import { tr } from "date-fns/locale"
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight } from "lucide-react"
import { DateRange } from "react-day-picker"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover"

interface DatePickerWithRangeProps extends React.HTMLAttributes<HTMLDivElement> {
    date: DateRange | undefined;
    setDate: (date: DateRange | undefined) => void;
}

const PRESETS = [
    { label: "Bugün", getValue: () => ({ from: startOfToday(), to: endOfToday() }) },
    { label: "Dün", getValue: () => ({ from: subDays(startOfToday(), 1), to: subDays(endOfToday(), 1) }) },
    { label: "Son 7 Gün", getValue: () => ({ from: subDays(startOfToday(), 7), to: endOfToday() }) },
    { label: "Son 30 Gün", getValue: () => ({ from: subDays(startOfToday(), 30), to: endOfToday() }) },
    { label: "Bu Ay", getValue: () => ({ from: startOfMonth(startOfToday()), to: endOfMonth(startOfToday()) }) },
    {
        label: "Geçen Ay", getValue: () => {
            const startOfLastMonth = startOfMonth(subMonths(startOfToday(), 1));
            const endOfLastMonth = endOfMonth(subMonths(startOfToday(), 1));
            return { from: startOfLastMonth, to: endOfLastMonth };
        }
    },
];

export function DatePickerWithRange({
    className,
    date,
    setDate,
}: DatePickerWithRangeProps) {
    const [isOpen, setIsOpen] = React.useState(false);
    const [tempDate, setTempDate] = React.useState<DateRange | undefined>(date);
    const [activePreset, setActivePreset] = React.useState<string | null>(null);

    // When popover opens, sync temp date with actual date
    React.useEffect(() => {
        if (isOpen) {
            setTempDate(date);
            setActivePreset(null);
        }
    }, [isOpen, date]);

    const handleApply = () => {
        setDate(tempDate);
        setIsOpen(false);
    };

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
                        <CalendarIcon className="mr-2 h-4 w-4 text-blue-400 group-hover:text-blue-300" />
                        {date?.from ? (
                            date.to ? (
                                <>
                                    {format(date.from, "dd MMM yyyy", { locale: tr })} -{" "}
                                    {format(date.to, "dd MMM yyyy", { locale: tr })}
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
                        {/* Presets Sidebar */}
                        <div className="flex sm:flex-col p-3 border-b sm:border-b-0 sm:border-r border-white/10 bg-black/20 min-w-[140px] overflow-x-auto sm:overflow-x-visible gap-1.5 align-top">
                            <div className="text-[11px] font-semibold text-white/40 uppercase tracking-widest mb-2 px-2 hidden sm:block">Hızlı Seçim</div>
                            {PRESETS.map((preset) => {
                                const isActive = activePreset === preset.label;
                                return (
                                    <button
                                        key={preset.label}
                                        onClick={() => {
                                            setTempDate(preset.getValue());
                                            setActivePreset(preset.label);
                                        }}
                                        className={cn(
                                            "px-3 py-2 text-[13px] text-left rounded-lg transition-all duration-200 whitespace-nowrap sm:whitespace-normal font-medium",
                                            isActive
                                                ? "bg-blue-600/20 text-blue-400 ring-1 ring-blue-500/30"
                                                : "text-white/70 hover:bg-white/10 hover:text-white"
                                        )}
                                    >
                                        {preset.label}
                                    </button>
                                );
                            })}
                        </div>

                        {/* Calendar View */}
                        <div className="p-4 bg-navy-950">
                            <Calendar
                                initialFocus
                                mode="range"
                                defaultMonth={tempDate?.from}
                                selected={tempDate}
                                onSelect={(range) => {
                                    setTempDate(range);
                                    setActivePreset(null);
                                }}
                                numberOfMonths={2}
                                locale={tr}
                                className="bg-transparent text-white"
                            />

                            <div className="flex items-center justify-between pt-4 border-t border-white/10 mt-4">
                                <div className="text-[13px] text-white/50 font-medium bg-black/20 px-3 py-1.5 rounded-md border border-white/5">
                                    {tempDate?.from ? (
                                        tempDate.to ? (
                                            <>
                                                <span className="text-white/80">{format(tempDate.from, "dd MMM yyyy", { locale: tr })}</span>
                                                <span className="mx-2 text-white/30">→</span>
                                                <span className="text-white/80">{format(tempDate.to, "dd MMM yyyy", { locale: tr })}</span>
                                            </>
                                        ) : (
                                            <span className="text-white/80">{format(tempDate.from, "dd MMM yyyy", { locale: tr })}</span>
                                        )
                                    ) : (
                                        "Lütfen bir tarih seçin"
                                    )}
                                </div>
                                <div className="flex justify-end gap-2">
                                    <Button size="sm" variant="ghost" className="text-[13px] text-white/70 hover:text-white hover:bg-white/10 h-8 px-4 rounded-md" onClick={() => setIsOpen(false)}>
                                        İptal
                                    </Button>
                                    <Button size="sm" className="h-8 px-5 text-[13px] font-medium bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/20 border-0 rounded-md transition-all" onClick={handleApply}>
                                        Uygula
                                    </Button>
                                </div>
                            </div>
                        </div>
                    </div>
                </PopoverContent>
            </Popover>
        </div>
    )
}
