import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";

import { QueryProvider } from "@/lib/query-provider";
import "./globals.css";

export const metadata: Metadata = {
  title: "LLM Insight Studio",
  description:
    "Research-grade NLP comparison platform across classification, summarization, QA and instruct lanes.",
};

const NAV = [
  { href: "/", label: "Overview" },
  { href: "/datasets", label: "Datasets" },
  { href: "/experiments/new", label: "New experiment" },
  { href: "/compare", label: "Compare" },
  { href: "/settings", label: "Settings" },
];

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>
          <div className="mx-auto flex min-h-screen max-w-6xl flex-col">
            <header className="border-b border-slate-200 px-6 py-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <Link href="/" className="text-xl font-semibold tracking-tight">
                  LLM Insight Studio
                </Link>
                <nav className="flex flex-wrap gap-4 text-sm">
                  {NAV.map((item) => (
                    <Link
                      key={item.href}
                      href={item.href}
                      className="text-slate-600 hover:text-brand-600"
                    >
                      {item.label}
                    </Link>
                  ))}
                </nav>
              </div>
            </header>
            <main className="flex-1 px-6 py-8">{children}</main>
            <footer className="border-t border-slate-200 px-6 py-4 text-xs text-slate-500">
              Research-grade comparison across four NLP task lanes.
            </footer>
          </div>
        </QueryProvider>
      </body>
    </html>
  );
}
