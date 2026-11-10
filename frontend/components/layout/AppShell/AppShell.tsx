"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { APP_NAME, NAV_ITEMS } from "@/lib/constants";

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <nav
          aria-label="Main"
          className="mx-auto flex max-w-6xl flex-wrap items-center gap-4 px-4 py-3"
        >
          <span className="text-lg font-semibold">{APP_NAME}</span>
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              aria-current={pathname === item.href ? "page" : undefined}
              className="text-sm text-slate-700 hover:text-blue-800 aria-[current=page]:font-semibold aria-[current=page]:text-blue-800"
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
    </div>
  );
}
