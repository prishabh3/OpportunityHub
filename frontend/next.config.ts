import type { NextConfig } from "next";

/**
 * Security response headers applied to every page and API route.
 *
 * CSP note: Next.js injects inline <script> tags for hydration, so a strict
 * nonce-based CSP requires custom middleware to generate and propagate the
 * nonce per-request.  The policy below is a pragmatic baseline that covers
 * the most impactful attack vectors (framing, MIME sniffing, cross-origin data
 * leakage) without blocking the Next.js runtime.
 * Upgrade to a nonce-based strict-dynamic CSP when the team has bandwidth.
 */
const securityHeaders = [
  // Force HTTPS for two years incl. subdomains, and allow preload-list inclusion.
  // Vercel already serves over HTTPS; this makes the browser refuse HTTP outright.
  {
    key: "Strict-Transport-Security",
    value: "max-age=63072000; includeSubDomains; preload",
  },
  // Prevent MIME-type sniffing.
  { key: "X-Content-Type-Options", value: "nosniff" },
  // Block framing (clickjacking). frame-ancestors in CSP covers modern browsers;
  // X-Frame-Options covers IE/older Safari.
  { key: "X-Frame-Options", value: "DENY" },
  // Only send origin in Referer — never the full URL with path/query/fragments.
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  // Disable hardware APIs this site never uses.
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), payment=()" },
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      // Next.js injects inline scripts; 'unsafe-inline' is required until nonces are added.
      "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: https:",
      "font-src 'self' https:",
      // API calls: Next.js rewrites + Supabase + backend.
      "connect-src 'self' https:",
      "object-src 'none'",
      "base-uri 'self'",
      "form-action 'self'",
      // Critical: prevents this page from being embedded in any iframe.
      "frame-ancestors 'none'",
    ].join("; "),
  },
];

const nextConfig: NextConfig = {
  // Remove the "X-Powered-By: Next.js" header to reduce framework fingerprinting.
  poweredByHeader: false,

  async headers() {
    return [
      {
        source: "/(.*)",
        headers: securityHeaders,
      },
    ];
  },
};

export default nextConfig;
