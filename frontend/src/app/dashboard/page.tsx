import type { Metadata } from "next";
import Link from "next/link";
import { Bookmark, Compass, User } from "lucide-react";

import { Navbar } from "@/components/layout/navbar";
import { Card } from "@/components/ui/card";
import { Recommendations } from "@/features/recommendations/components/recommendations";
import { createClient } from "@/lib/supabase/server";

export const metadata: Metadata = { title: "Dashboard — OpportunityHub" };

const QUICK_LINKS = [
  { href: "/opportunities", label: "Browse opportunities", icon: Compass },
  { href: "/bookmarks", label: "Your bookmarks", icon: Bookmark },
  { href: "/profile", label: "Edit profile", icon: User },
];

export default async function DashboardPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  const name = user?.email?.split("@")[0] ?? "there";

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 py-10">
        <h1 className="text-3xl font-semibold tracking-tight">Welcome back, {name}</h1>
        <p className="mt-1 text-muted-foreground">Here&apos;s what&apos;s relevant to you.</p>

        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          {QUICK_LINKS.map(({ href, label, icon: Icon }) => (
            <Link key={href} href={href}>
              <Card className="flex items-center gap-3 p-4 transition-colors hover:border-primary/50">
                <span className="flex size-9 items-center justify-center rounded-lg bg-muted">
                  <Icon className="size-4 text-primary" />
                </span>
                <span className="text-sm font-medium">{label}</span>
              </Card>
            </Link>
          ))}
        </div>

        <section className="mt-10">
          <h2 className="mb-4 text-xl font-semibold tracking-tight">Recommended for you</h2>
          <Recommendations />
        </section>
      </main>
    </>
  );
}
