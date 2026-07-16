import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "QuoteIQ | AI Quote-to-Order Platform",
  description: "AI-assisted RFQ extraction, pricing, approvals, analytics, and ERP-ready order automation.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col font-sans">{children}</body>
    </html>
  );
}
