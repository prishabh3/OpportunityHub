import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";

export function Cta({ isAuthenticated }: { isAuthenticated: boolean }) {
  return (
    <section className="px-6 py-20">
      <div className="mx-auto max-w-4xl rounded-2xl border border-border/60 bg-card/50 px-8 py-16 text-center">
        <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
          Stop checking 30 tabs every morning.
        </h2>
        <p className="mx-auto mt-4 max-w-xl text-muted-foreground">
          Create your profile once. We&apos;ll surface what&apos;s relevant and tell you when
          it&apos;s about to expire.
        </p>
        <div className="mt-8 flex justify-center">
          {isAuthenticated ? (
            <Button size="lg" nativeButton={false} render={<Link href="/dashboard" />}>
              Go to your dashboard <ArrowRight className="ml-1 size-4" />
            </Button>
          ) : (
            <Button size="lg" nativeButton={false} render={<Link href="/sign-up" />}>
              Create your free account <ArrowRight className="ml-1 size-4" />
            </Button>
          )}
        </div>
      </div>
    </section>
  );
}
