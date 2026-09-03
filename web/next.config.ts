import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    const flask = process.env.FLASK_ORIGIN ?? "http://127.0.0.1:5000";
    return [{ source: "/api/:path*", destination: `${flask}/api/:path*` }];
  },
};

export default nextConfig;
