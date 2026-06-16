import Image from "next/image";
import Link from "next/link";
import { redirect } from "next/navigation";

import { createClient } from "@/lib/supabase/server";

export default async function AuthLayout({ children }: { children: React.ReactNode }) {
  // Already signed in? Don't show the auth forms — send them home.
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (user) redirect("/");

  return (
    <div className="flex min-h-svh flex-col items-center justify-center px-4 py-12">
      <Link href="/" className="mb-8 flex items-center gap-2 font-semibold">
        <Image src="/logo.png" alt="OpportunityHub" width={28} height={28} priority />
        OpportunityHub
      </Link>
      <div className="w-full max-w-sm">{children}</div>
    </div>
  );
}
