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
  description: "Chaser: Chase your life!",
  icons: {
    icon: [
      { url: '/chaser-whitebg.png', media: '(prefers-color-scheme: dark)' },
      { url: '/chaser-blackbg.png', media: '(prefers-color-scheme: light)' },
      { url: '/chaser.ico', sizes: 'any' }
    ],
    shortcut: '/chaser.ico',
    apple: [
      { url: '/chaser-whitebg.png', media: '(prefers-color-scheme: dark)' },
      { url: '/chaser-blackbg.png', media: '(prefers-color-scheme: light)' }
    ],
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
