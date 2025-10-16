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
  title: "Chaser: Chase your life!",
  description: "Chaser: Chase your life!",
  // icon arrays with explicit sizes and type, plus a shortcut fallback and favicon.ico fallback
  icons: {
    icon: [
      { url: '/chaser-blackbg.png', sizes: 'any', type: 'image/png' },
      { url: '/chaser-whitebg.png', sizes: 'any', type: 'image/png' }
    ],
    shortcut: ['/favicon.ico', '/chaser-blackbg.png'], // shortcut favicon fallback(s)
    apple: [
      { url: '/chaser-whitebg.png', sizes: '180x180', type: 'image/png' },
      { url: '/chaser-blackbg.png', sizes: '180x180', type: 'image/png' }
    ]
  }
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
