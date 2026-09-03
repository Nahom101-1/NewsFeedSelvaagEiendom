import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Bundles only the files the server actually needs, so the production image
  // ships without node_modules. Cuts the image from ~1GB to well under 200MB.
  output: "standalone",

  async rewrites() {
    const flask = process.env.FLASK_ORIGIN ?? "http://127.0.0.1:5000";
    return [{ source: "/api/:path*", destination: `${flask}/api/:path*` }];
  },
};

export default nextConfig;
