import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/providers/theme-provider";
import { QueryProvider } from "@/components/providers/query-provider";
import { Toaster } from "@/components/ui/sonner";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const SITE_DESCRIPTION =
  "OpportunityHub aggregates hackathons, internships, jobs, research programs, and competitions from across the internet into one personalized feed.";

export const metadata: Metadata = {
  metadataBase: new URL("https://opportunity-hub-opal.vercel.app"),
  title: "OpportunityHub — Never miss an opportunity",
  description: SITE_DESCRIPTION,
  openGraph: {
    title: "OpportunityHub — Never miss an opportunity",
    description: SITE_DESCRIPTION,
    url: "/",
    siteName: "OpportunityHub",
    images: [{ url: "/logo.png", width: 512, height: 512, alt: "OpportunityHub" }],
    type: "website",
  },
  twitter: {
    card: "summary",
    title: "OpportunityHub — Never miss an opportunity",
    description: SITE_DESCRIPTION,
    images: ["/logo.png"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col bg-background text-foreground">
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem disableTransitionOnChange>
          <QueryProvider>
            {children}
            <Toaster />
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
