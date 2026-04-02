"use client";

import { useState, useEffect } from "react";
import { Sidebar } from "@/components/dashboard/Sidebar";
import { Topbar } from "@/components/dashboard/Topbar";
import OnboardingWizard from "@/components/onboarding/OnboardingWizard";
import GlobalCostPopup from "@/components/dashboard/GlobalCostPopup";
import { api } from "@/lib/api";
import "flag-icons/css/flag-icons.min.css";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const [mobileNavOpen, setMobileNavOpen] = useState(false);
    const [onboardingStatus, setOnboardingStatus] = useState<string | null>(null);
    const [checking, setChecking] = useState(true);

    useEffect(() => {
        async function checkOnboarding() {
            try {
                // Get fresh user data to check onboarding status
                const user = await api.get("/auth/me/");
                setOnboardingStatus(user.onboarding_status || "WELCOME");
                
                // Update localStorage with fresh data
                localStorage.setItem("user", JSON.stringify(user));
            } catch (error) {
                console.error("Failed to check onboarding status", error);
                // If it fails, we might be unauthenticated, which is handled elsewhere or via 401
            } finally {
                setChecking(false);
            }
        }
        checkOnboarding();
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
            <GlobalCostPopup />
            {onboardingStatus && onboardingStatus !== "COMPLETED" && (
                <OnboardingWizard 
                    initialStatus={onboardingStatus}
                    onComplete={() => setOnboardingStatus("COMPLETED")} 
                />
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
