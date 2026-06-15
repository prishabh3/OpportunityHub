import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { Hero } from "@/components/marketing/hero";
import { SourceStrip } from "@/components/marketing/source-strip";
import { FeatureGrid } from "@/components/marketing/feature-grid";
import { Cta } from "@/components/marketing/cta";

export default function Home() {
  return (
    <>
      <Navbar />
      <main className="flex-1">
        <Hero />
        <SourceStrip />
        <FeatureGrid />
        <Cta />
      </main>
      <Footer />
    </>
  );
}
