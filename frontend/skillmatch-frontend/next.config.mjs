/** @type {import('next').NextConfig} */

// Security headers applied to every response. The CSP allows the Next.js
// dev overlay (`'unsafe-eval'` / `'unsafe-inline'`) so hot-reload keeps
// working locally; those two directives are the standard trade-off the
// Next.js docs recommend for App-Router dev. `connect-src` must include the
// backend origin the client talks to (defaults to localhost:8000).
const API_ORIGIN = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const SECURITY_HEADERS = [
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: blob: " + API_ORIGIN,
      "font-src 'self' data:",
      "connect-src 'self' " + API_ORIGIN,
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'",
    ].join("; "),
  },
  { key: "X-Content-Type-Options",   value: "nosniff" },
  { key: "X-Frame-Options",          value: "DENY" },
  { key: "Referrer-Policy",          value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy",       value: "camera=(), microphone=(), geolocation=()" },
  {
    key: "Strict-Transport-Security",
    value: "max-age=63072000; includeSubDomains; preload",
  },
];

const nextConfig = {
  reactStrictMode: true,
  async headers() {
    return [
      { source: "/:path*", headers: SECURITY_HEADERS },
    ];
  },
};

export default nextConfig;
