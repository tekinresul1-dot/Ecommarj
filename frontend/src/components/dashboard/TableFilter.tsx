"use client";

import { useState } from "react";
import { Trash2, Search, ChevronDown, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import clsx from "clsx";

export type FilterType = "text" | "number" | "date";

export interface FilterColumn {
    id: string;
    label: string;
    type: FilterType;
}

export interface FilterState {
    columnId: string;
    operator: string;
    value: string;
}

interface TableFilterProps {
    columns: FilterColumn[];
    onApply: (filter: FilterState | null) => void;
    onClose?: () => void;
}

export function TableFilter({ columns, onApply, onClose }: TableFilterProps) {
    const defaultColumn = columns[0]?.id || "";
    const [columnId, setColumnId] = useState<string>(defaultColumn);
    const [operator, setOperator] = useState<string>("contains");
    const [value, setValue] = useState<string>("");

    const [isColumnDropdownOpen, setColumnDropdownOpen] = useState(false);
    const [isOperatorDropdownOpen, setOperatorDropdownOpen] = useState(false);

    const activeColumn = columns.find(c => c.id === columnId);

    const handleApply = () => {
        if (!value.trim()) {
            onApply(null);
            return;
        }
        onApply({ columnId, operator, value });
    };

    const handleClear = () => {
        setValue("");
        onApply(null);
        if (onClose) onClose();
    };

    const textOperators = [
        { value: "contains", label: "İçerir" },
        { value: "equals", label: "Eşittir" },
    ];

    const numberOperators = [
        { value: "equals", label: "Eşittir" },
        { value: "greater", label: "Büyüktür" },
        { value: "less", label: "Küçüktür" },
    ];

    const currentOperators = activeColumn?.type === "number" ? numberOperators : textOperators;

    // Ensure operator is valid for current column type
    if (!currentOperators.find(o => o.value === operator)) {
        setOperator(currentOperators[0].value);
    }

    return (
        <div className="flex flex-wrap items-center gap-2 bg-navy-800/40 p-2 rounded-lg border border-white/5 animate-in fade-in slide-in-from-top-2 duration-200">
            <button
                onClick={handleClear}
                className="flex items-center justify-center w-10 h-10 rounded-lg bg-red-500/10 text-red-500 hover:bg-red-500 hover:text-white transition-colors border border-red-500/20"
                title="Filtreyi Temizle"
            >
                <Trash2 className="w-4 h-4" />
            </button>

            {/* Column Selector */}
            <div className="relative min-w-[200px]">
                <button
                    onClick={() => setColumnDropdownOpen(!isColumnDropdownOpen)}
                    onBlur={() => setTimeout(() => setColumnDropdownOpen(false), 200)}
                    className="w-full flex items-center justify-between gap-2 px-4 h-10 bg-navy-950 border border-white/10 rounded-lg text-sm text-white/90 hover:border-white/20 transition-colors"
                >
                    <span className="truncate">{activeColumn?.label || "Kolon Seçin"}</span>
                    <ChevronDown className={clsx("w-4 h-4 text-white/40 transition-transform", isColumnDropdownOpen && "rotate-180")} />
                </button>
                {isColumnDropdownOpen && (
                    <div className="absolute top-full left-0 mt-1 w-full bg-navy-900 border border-white/10 rounded-lg shadow-xl z-50 overflow-hidden py-1">
                        {columns.map(col => (
                            <button
                                key={col.id}
                                onMouseDown={(e) => {
                                    e.preventDefault();
                                    setColumnId(col.id);
                                    setColumnDropdownOpen(false);
                                }}
                                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-left hover:bg-white/5 transition-colors"
                            >
                                <div className="w-4 flex items-center justify-center">
                                    {columnId === col.id && <Check className="w-3.5 h-3.5 text-blue-400" />}
                                </div>
                                <span className={clsx(columnId === col.id ? "text-white font-medium" : "text-white/70")}>
                                    {col.label}
                                </span>
                            </button>
                        ))}
                    </div>
                )}
            </div>

            {/* Operator Selector */}
            <div className="relative min-w-[140px]">
                <button
                    onClick={() => setOperatorDropdownOpen(!isOperatorDropdownOpen)}
                    onBlur={() => setTimeout(() => setOperatorDropdownOpen(false), 200)}
                    className="w-full flex items-center justify-between gap-2 px-4 h-10 bg-navy-950 border border-white/10 rounded-lg text-sm text-white/90 hover:border-white/20 transition-colors"
                >
                    <span>{currentOperators.find(o => o.value === operator)?.label}</span>
                    <ChevronDown className={clsx("w-4 h-4 text-white/40 transition-transform", isOperatorDropdownOpen && "rotate-180")} />
                </button>
                {isOperatorDropdownOpen && (
                    <div className="absolute top-full left-0 mt-1 w-full bg-navy-900 border border-white/10 rounded-lg shadow-xl z-50 overflow-hidden py-1">
                        {currentOperators.map(op => (
                            <button
                                key={op.value}
                                onMouseDown={(e) => {
                                    e.preventDefault();
                                    setOperator(op.value);
                                    setOperatorDropdownOpen(false);
                                }}
                                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-left hover:bg-white/5 transition-colors"
                            >
                                <div className="w-4 flex items-center justify-center">
                                    {operator === op.value && <Check className="w-3.5 h-3.5 text-blue-400" />}
                                </div>
                                <span className={clsx(operator === op.value ? "text-white font-medium" : "text-white/70")}>
                                    {op.label}
                                </span>
                            </button>
                        ))}
                    </div>
                )}
            </div>

            {/* Input Value */}
            <div className="relative flex-1 min-w-[200px]">
                <div className="absolute inset-y-0 right-3 flex items-center pointer-events-none">
                    <Search className="w-4 h-4 text-white/30" />
                </div>
                <input
                    type={activeColumn?.type === "number" ? "number" : "text"}
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleApply()}
                    placeholder="Filtreleme kriteri"
                    className="w-full h-10 bg-navy-950 border border-white/10 rounded-lg pl-4 pr-10 text-sm text-white focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50 transition-all placeholder:text-white/30"
                />
            </div>

            {/* Apply Button */}
            <Button
                onClick={handleApply}
                className="h-10 px-6 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white border-0 shadow-lg shadow-blue-900/20"
            >
                Filtrele
            </Button>
        </div>
    );
}

// Utility function to apply the filter to an array of objects
export function applyTableFilter<T>(data: T[], filter: FilterState | null): T[] {
    if (!filter || !filter.value.trim()) return data;

    const { columnId, operator, value } = filter;
    const searchVal = value.toLowerCase().trim();

    return data.filter((item) => {
        const itemVal = item[columnId as keyof T];

        // Handle null/undefined
        if (itemVal === null || itemVal === undefined) return false;

        // Number comparison
        if (operator === "greater") return Number(itemVal) > Number(searchVal);
        if (operator === "less") return Number(itemVal) < Number(searchVal);
        if (operator === "equals" && !isNaN(Number(searchVal))) {
            // Let's also do string strictly equals for non-numbers, but for numbers we can cast
            if (typeof itemVal === 'number' || !isNaN(Number(itemVal))) {
                return Number(itemVal) === Number(searchVal);
            }
            return String(itemVal).toLowerCase() === searchVal;
        }

        // String comparison fallback
        const strVal = String(itemVal).toLowerCase();

        if (operator === "contains") {
            return strVal.includes(searchVal);
        }
        if (operator === "equals") {
            return strVal === searchVal;
        }

        return true;
    });
}
