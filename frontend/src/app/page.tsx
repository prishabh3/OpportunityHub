import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { Hero } from "@/components/marketing/hero";
import { SourceStrip } from "@/components/marketing/source-strip";
import { FeatureGrid } from "@/components/marketing/feature-grid";
import { Cta } from "@/components/marketing/cta";
import { createClient } from "@/lib/supabase/server";

export default async function Home() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  const isAuthenticated = !!user;

  return (
    <>
      <Navbar />
      <main className="flex-1">
        <Hero isAuthenticated={isAuthenticated} />
        <SourceStrip />
        <FeatureGrid />
        <Cta isAuthenticated={isAuthenticated} />
      </main>
      <Footer />
    </>
  );
}
