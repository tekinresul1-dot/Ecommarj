import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  skipTrailingSlashRedirect: true,
  async rewrites() {
    // Internal Docker hostname for server-side proxying
    const internalBackend = "http://backend:8000";
    // Public API URL for fallback
    const publicApi = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api").replace(/\/$/, "");
    
    return [
      // 1. Django Admin Paths (Must be first to take precedence)
      { source: "/admin/:path*/", destination: `${internalBackend}/admin/:path*/` },
      { source: "/admin/:path*", destination: `${internalBackend}/admin/:path*` },
      
      // 2. Django Static Files (For admin CSS/JS)
      { source: "/static/:path*/", destination: `${internalBackend}/static/:path*/` },
      { source: "/static/:path*", destination: `${internalBackend}/static/:path*` },
      
      // 3. API Paths
      { source: "/api/:path*/", destination: `${publicApi}/:path*/` },
      { source: "/api/:path*", destination: `${publicApi}/:path*` },
    ];
  },
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "cdn.dsmcdn.com",
      },
      {
        protocol: "https",
        hostname: "img-trendyol.mncdn.com",
      },
    ],
  },
  // Empty turbopack config to use Turbopack (Next.js 16 default) without errors
  turbopack: {},
};

export default nextConfig;
