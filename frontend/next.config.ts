import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  skipTrailingSlashRedirect: true,
  async rewrites() {
    const backend = (process.env.NEXT_PUBLIC_API_URL || "http://backend:8000/api").replace(/\/$/, "");
    return [
      // Match paths with trailing slash first — preserve it
      { source: "/api/:path*/", destination: `${backend}/:path*/` },
      // Match paths without trailing slash — forward as-is
      { source: "/api/:path*", destination: `${backend}/:path*` },
    ];
  },
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "cdn.dsmcdn.com",
      },
    ],
  },
  // Empty turbopack config to use Turbopack (Next.js 16 default) without errors
  turbopack: {},
};

export default nextConfig;
