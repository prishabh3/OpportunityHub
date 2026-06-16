import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { Navbar } from "@/components/layout/navbar";
import { AdminDashboard } from "@/features/admin/components/admin-dashboard";
import { createClient } from "@/lib/supabase/server";

export const metadata: Metadata = { title: "Admin — OpportunityHub" };

export default async function AdminPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  // Proxy already requires auth on /admin; here we additionally require the
  // admin role (set via the user's Supabase app_metadata).
  const role = (user?.app_metadata as { role?: string } | undefined)?.role;
  if (role !== "admin") redirect("/");

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-5xl px-4 py-10">
        <h1 className="mb-8 text-3xl font-semibold tracking-tight">Admin</h1>
        <AdminDashboard />
      </main>
    </>
  );
}
