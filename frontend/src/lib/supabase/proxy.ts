import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";
import { env } from "@/lib/env";

const PROTECTED_PREFIXES = ["/dashboard", "/bookmarks", "/profile", "/notifications", "/admin"];

/**
 * Refreshes the Supabase session cookie on every request, redirects
 * unauthenticated users away from protected routes, and enforces MFA
 * (aal2) for users who have enrolled a TOTP factor.
 */
export async function updateSession(request: NextRequest) {
  let response = NextResponse.next({ request });

  const supabase = createServerClient(
    env.NEXT_PUBLIC_SUPABASE_URL,
    env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value));
          response = NextResponse.next({ request });
          cookiesToSet.forEach(({ name, value, options }) =>
            response.cookies.set(name, value, options)
          );
        },
      },
    }
  );

  // getUser() validates the JWT with Supabase's server — unlike getSession()
  // which only reads the cookie and trusts the local value without re-checking.
  const { data } = await supabase.auth.getUser();

  const pathname = request.nextUrl.pathname;
  const isProtected = PROTECTED_PREFIXES.some((prefix) => pathname.startsWith(prefix));

  // 1. Unauthenticated → redirect to sign-in.
  if (!data.user && isProtected) {
    const redirectUrl = new URL("/sign-in", request.url);
    redirectUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(redirectUrl);
  }

  // 2. Authenticated + on a protected route + MFA enrolled but not yet verified →
  //    redirect to the MFA challenge page.
  //    Only check protected routes: avoids an extra Supabase round-trip on every
  //    public page (homepage, /opportunities, etc.) for logged-in users.
  if (data.user && isProtected) {
    const { data: aal } = await supabase.auth.mfa.getAuthenticatorAssuranceLevel();
    if (aal?.nextLevel === "aal2" && aal?.currentLevel !== "aal2") {
      const mfaUrl = new URL("/mfa-challenge", request.url);
      mfaUrl.searchParams.set("next", pathname);
      return NextResponse.redirect(mfaUrl);
    }
  }

  return response;
}
