import type { Metadata } from "next";
import "./globals.css";

// The browser-tab icon is app/icon.svg (the Landed "L" mark); Next.js picks it up by its name.
export const metadata: Metadata = {
  title: "Landed",
  description: "Find CS internships and new-grad roles, track every application, and land the offer.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
