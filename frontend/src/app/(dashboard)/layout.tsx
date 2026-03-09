"use client";

import { useState, useEffect } from "react";
import { Sidebar } from "@/components/dashboard/Sidebar";
import { Topbar } from "@/components/dashboard/Topbar";
import OnboardingWizard from "@/components/onboarding/OnboardingWizard";
import { api } from "@/lib/api";
import "flag-icons/css/flag-icons.min.css";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const [mobileNavOpen, setMobileNavOpen] = useState(false);
    const [needsOnboarding, setNeedsOnboarding] = useState<boolean>(false);
    const [checking, setChecking] = useState(true);

    useEffect(() => {
        async function checkCreds() {
            try {
                const res = await api.get("/integrations/trendyol/save-credentials/");
                if (!res.api_key) {
                    setNeedsOnboarding(true);
                }
            } catch (error) {
                console.error("Failed to check credentials", error);
            } finally {
                setChecking(false);
            }
        }
        checkCreds();
    }, []);

    if (checking) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-[#070B14]">
                <div className="w-8 h-8 rounded-full border-t-2 border-accent-500 animate-spin"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#070B14] selection:bg-accent-500/30 font-sans">
            {needsOnboarding && (
                <OnboardingWizard onComplete={() => setNeedsOnboarding(false)} />
            )}

            <Sidebar mobileNavOpen={mobileNavOpen} setMobileNavOpen={setMobileNavOpen} />

            <div className="lg:pl-72 flex flex-col min-h-screen">
                <Topbar setMobileNavOpen={setMobileNavOpen} />

                <main className="flex-1 overflow-x-hidden">
                    {children}
                </main>
            </div>
        </div>
    );
}
