import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Chaser: chase your life!",
  description: "PTT股票版智能分析平台 - 追蹤投資機會，掌握市場脈動",
  icons: {
    icon: [
      { url: '/favicon.ico', sizes: 'any' },
      { url: '/chaser-logo.png', type: 'image/png' }
    ],
    shortcut: '/favicon.ico',
    apple: '/chaser-logo.png',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
