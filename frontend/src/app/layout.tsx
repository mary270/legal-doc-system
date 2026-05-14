import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Pearson Specter Litt — Legal Intelligence',
  description: 'AI-powered legal document intelligence platform for elite law firms',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${inter.className} bg-bg-primary text-text-primary min-h-screen antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
