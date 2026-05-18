/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const backend = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    return [
      {
        source: "/api/nexus/:path*",
        destination: `${backend}/:path*`,
      },
    ];
  },
};

export default nextConfig;
