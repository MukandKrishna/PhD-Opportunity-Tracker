import type { Metadata } from "next";
import Link from "next/link";

import "./globals.css";

export const metadata: Metadata = {
  title: "PhD Opportunity Tracker",
  description: "Track active AI, CS, ML, DL, Agents, and RAG PhD opportunities.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <header className="topbar">
          <div className="shell topbar-inner">
            <div className="brand">
              <span className="brand-mark">PhD Tracker</span>
            </div>
            <nav className="nav-links">
              <Link className="nav-chip" href="/">
                All Opportunities
              </Link>
              <Link className="nav-chip" href="/applied">
                Applied
              </Link>
            </nav>
          </div>
        </header>
        {children}
      </body>
    </html>
  );
}
