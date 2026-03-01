export function formatCurrency(value: number | string | undefined): string {
    if (value === undefined || value === null) return "₺0,00";
    const num = typeof value === "string" ? parseFloat(value) : value;
    if (isNaN(num)) return "₺0,00";

    return new Intl.NumberFormat('tr-TR', {
        style: 'currency',
        currency: 'TRY',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(num);
}

export function formatPercentage(value: number | string | undefined): string {
    if (value === undefined || value === null) return "%0,00";
    const num = typeof value === "string" ? parseFloat(value) : value;
    if (isNaN(num)) return "%0,00";

    return `%${new Intl.NumberFormat('tr-TR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(num)}`;
}
