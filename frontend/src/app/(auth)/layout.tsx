import Image from "next/image";
import Link from "next/link";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
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
