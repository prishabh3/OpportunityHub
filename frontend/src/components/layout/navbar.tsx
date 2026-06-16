import Image from "next/image";
import Link from "next/link";
import { Search as SearchIcon } from "lucide-react";
import { Button } from "@/components/ui/button";

import { UserMenu } from "@/features/auth/components/user-menu";
import { NotificationBell } from "@/features/notifications/components/notification-bell";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { createClient } from "@/lib/supabase/server";

const links = [
  { href: "/opportunities?category=hackathons", label: "Hackathons" },
  { href: "/opportunities?category=jobs", label: "Jobs" },
];

export async function Navbar() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight">
          <Image src="/logo.png" alt="OpportunityHub" width={28} height={28} priority />
          OpportunityHub
        </Link>

        <nav className="hidden items-center gap-8 text-sm text-muted-foreground md:flex">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="transition-colors hover:text-foreground"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <Link
            href="/search"
            aria-label="Search"
            className="flex size-9 items-center justify-center rounded-md text-muted-foreground hover:text-foreground"
          >
            <SearchIcon className="size-5" />
          </Link>
          <ThemeToggle />
          {user ? (
            <>
              <NotificationBell />
              <UserMenu
                email={user.email ?? "account"}
                isAdmin={
                  (user.app_metadata as { role?: string } | undefined)?.role === "admin"
                }
              />
            </>
          ) : (
            <>
              <Button variant="ghost" nativeButton={false} render={<Link href="/sign-in" />}>
                Sign in
              </Button>
              <Button nativeButton={false} render={<Link href="/sign-up" />}>
                Get started
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
