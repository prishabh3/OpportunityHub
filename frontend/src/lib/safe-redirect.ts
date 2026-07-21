/**
 * Validates a caller-supplied post-authentication redirect target.
 *
 * A `startsWith("/")` check is not sufficient. `//evil.com` also starts with a
 * slash, but it is a *protocol-relative* URL: the browser resolves it against
 * the current scheme and navigates off-site. `/\evil.com` is treated the same
 * way by several browsers, which normalize the backslash to a slash. Either one
 * turns our own sign-in flow into a phishing redirector — the victim follows a
 * link to the real site, authenticates for real, and lands on the attacker's
 * page (CWE-601).
 *
 * Only same-origin *paths* are accepted; anything else falls back to "/".
 */
export function safeRedirectPath(value: string | null | undefined, fallback = "/"): string {
  if (!value) return fallback;

  // Must be a rooted path, and the second character must not turn it into a
  // network-path reference ("//host" or the "/\host" variant).
  if (!value.startsWith("/")) return fallback;
  if (value[1] === "/" || value[1] === "\\") return fallback;

  // Control characters (notably \t \r \n) are stripped by browsers before URL
  // parsing, so "/\t/evil.com" would slip past the check above.
  if (/[\u0000-\u0020]/.test(value)) return fallback;

  return value;
}
