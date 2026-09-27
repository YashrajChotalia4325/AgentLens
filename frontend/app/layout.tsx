import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgentLens",
  description: "Tracing, evaluation and regression testing for an AI agent",
};

// Every page shows live data from the API, so never pre-render at build time.
export const dynamic = "force-dynamic";

const links = [
  { href: "/", label: "Overview" },
  { href: "/runs", label: "Runs" },
  { href: "/experiments", label: "Experiments" },
  { href: "/compare", label: "Compare" },
];

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="antialiased">
      <body className="min-h-screen font-sans">
        <header className="border-b border-line bg-surface">
          <nav className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
            <Link href="/" className="font-semibold">
              AgentLens
            </Link>
            {links.map((link) => (
              <Link key={link.href} href={link.href} className="text-sm text-ink-2 hover:text-ink">
                {link.label}
              </Link>
            ))}
          </nav>
        </header>
        <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
