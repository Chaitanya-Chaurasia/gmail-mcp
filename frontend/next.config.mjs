/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // proxy API calls to the FastAPI backend
    return [{ source: "/api/:path*", destination: "http://localhost:8000/api/:path*" }];
  },
};

export default nextConfig;
