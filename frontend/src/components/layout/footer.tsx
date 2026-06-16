import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-border/40 px-6 py-10">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 text-sm text-muted-foreground sm:flex-row">
        <p>&copy; {new Date().getFullYear()} OpportunityHub. All rights reserved.</p>
        <div className="flex gap-6">
          <Link href="/opportunities?category=hackathons" className="hover:text-foreground">
            Hackathons
          </Link>
          <Link href="/opportunities?category=jobs" className="hover:text-foreground">
            Jobs
          </Link>
          <Link href="/sign-in" className="hover:text-foreground">
            Sign in
          </Link>
        </div>
      </div>
    </footer>
  );
}
