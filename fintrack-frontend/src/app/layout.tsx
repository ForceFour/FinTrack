import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { Inter } from "next/font/google";
const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "FinTrack - AI-Powered Expense Tracker",
  description: "Multi-Agent AI Financial Analysis System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <link
        rel="icon"
        type="image/png"
        href="/favicon-96x96.png"
        sizes="96x96"
      />
      <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
      <link rel="shortcut icon" href="/favicon.ico" />
      <link
        rel="apple-touch-icon"
        sizes="180x180"
        href="/apple-touch-icon.png"
      />
      <meta name="apple-mobile-web-app-title" content="MyWebSite" />
      <link rel="manifest" href="/site.webmanifest" />
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
