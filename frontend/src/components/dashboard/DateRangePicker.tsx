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

    // When popover opens, sync temp date with actual date
    React.useEffect(() => {
        if (isOpen) {
            setTempDate(date);
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
                            "w-full sm:w-[280px] justify-start text-left font-normal bg-navy-950 border-white/10 text-white/90 hover:bg-white/5 hover:text-white hover:border-white/20 h-11 transition-colors",
                            !date && "text-muted-foreground"
                        )}
                    >
                        <CalendarIcon className="mr-2 h-4 w-4 text-blue-400" />
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
                    className="w-auto p-0 bg-navy-950 border-white/10 text-white shadow-2xl rounded-2xl overflow-hidden"
                    align="end"
                >
                    <div className="flex flex-col sm:flex-row">
                        {/* Presets Sidebar */}
                        <div className="flex sm:flex-col gap-1 p-2 border-b sm:border-b-0 sm:border-r border-white/10 bg-navy-900/50 min-w-[120px] overflow-x-auto sm:overflow-x-visible">
                            <div className="text-[11px] font-semibold text-white/50 uppercase tracking-wider mb-1 mt-1 px-3 hidden sm:block">Hızlı Seçim</div>
                            {PRESETS.map((preset) => (
                                <button
                                    key={preset.label}
                                    onClick={() => setTempDate(preset.getValue())}
                                    className="px-3 py-1.5 text-[13px] text-left rounded-md hover:bg-white/10 transition-colors whitespace-nowrap sm:whitespace-normal text-white/80 hover:text-white"
                                >
                                    {preset.label}
                                </button>
                            ))}
                        </div>

                        {/* Calendar View */}
                        <div className="p-2 sm:p-3">
                            <Calendar
                                initialFocus
                                mode="range"
                                defaultMonth={tempDate?.from}
                                selected={tempDate}
                                onSelect={setTempDate}
                                numberOfMonths={2}
                                locale={tr}
                                className="bg-transparent text-white"
                                classNames={{
                                    months: "flex flex-col sm:flex-row space-y-4 sm:space-x-4 sm:space-y-0",
                                    month: "space-y-3",
                                    caption: "flex justify-center pt-1 relative items-center",
                                    caption_label: "text-[13px] font-medium",
                                    nav: "space-x-1 flex items-center bg-white/5 rounded-md p-0.5",
                                    nav_button: "h-6 w-6 bg-transparent p-0 opacity-50 hover:opacity-100 hover:bg-white/10 rounded-sm transition-colors flex items-center justify-center",
                                    nav_button_previous: "absolute left-2",
                                    nav_button_next: "absolute right-2",
                                    table: "w-full border-collapse space-y-1",
                                    head_row: "flex",
                                    head_cell: "text-white/50 rounded-md w-7 font-normal text-[0.7rem] capitalize",
                                    row: "flex w-full mt-1.5",
                                    cell: "h-7 w-7 text-center text-[13px] p-0 relative [&:has([aria-selected].day-range-end)]:rounded-r-md [&:has([aria-selected].day-outside)]:bg-white/5 [&:has([aria-selected])]:bg-purple-600/20 first:[&:has([aria-selected])]:rounded-l-md last:[&:has([aria-selected])]:rounded-r-md focus-within:relative focus-within:z-20",
                                    day: "h-7 w-7 p-0 font-normal aria-selected:opacity-100 rounded-md hover:bg-white/10 transition-colors",
                                    day_range_end: "day-range-end",
                                    day_selected: "bg-purple-600 text-white hover:bg-purple-500 hover:text-white focus:bg-purple-600 focus:text-white",
                                    day_today: "bg-white/5 text-white font-bold",
                                    day_outside: "day-outside text-white/30 opacity-50 aria-selected:bg-white/10 aria-selected:text-white/50 aria-selected:opacity-30",
                                    day_disabled: "text-white/30 opacity-50",
                                    day_range_middle: "aria-selected:bg-purple-600/20 aria-selected:text-purple-200 aria-selected:rounded-none",
                                    day_hidden: "invisible",
                                }}
                            />

                            <div className="flex justify-end gap-2 pt-3 border-t border-white/10 mt-1">
                                <Button size="sm" variant="ghost" className="text-[13px] text-white/70 hover:text-white hover:bg-white/5 h-8 px-3" onClick={() => setIsOpen(false)}>
                                    İptal
                                </Button>
                                <Button size="sm" className="h-8 px-4 text-[13px] bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white shadow-lg border-0" onClick={handleApply}>
                                    Filtrele
                                </Button>
                            </div>
                        </div>
                    </div>
                </PopoverContent>
            </Popover>
        </div>
    )
}
