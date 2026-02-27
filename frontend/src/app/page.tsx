import Navbar from "@/components/Navbar";
import Hero from "@/components/Hero";
import Features from "@/components/Features";
import DashboardShowcase from "@/components/DashboardShowcase";
import HowItWorks from "@/components/HowItWorks";
import CTA from "@/components/CTA";
import Footer from "@/components/Footer";

export default function Home() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <Features />
        <DashboardShowcase />
        <HowItWorks />
        <CTA />
      </main>
      <Footer />
    </>
  );
}
