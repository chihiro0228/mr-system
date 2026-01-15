/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      // Local development
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/uploads/**',
      },
      // Local network access (for mobile testing)
      {
        protocol: 'http',
        hostname: '*.*.*.* ',
        port: '8000',
        pathname: '/uploads/**',
      },
      // Cloudinary (production)
      {
        protocol: 'https',
        hostname: 'res.cloudinary.com',
        pathname: '/**',
      },
      // Render backend (production)
      {
        protocol: 'https',
        hostname: '*.onrender.com',
        pathname: '/uploads/**',
      },
    ],
  },
};

export default nextConfig;
