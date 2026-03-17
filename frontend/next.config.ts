import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  skipTrailingSlashRedirect: true,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://backend:8000/api"}/:path*`,
      },
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
