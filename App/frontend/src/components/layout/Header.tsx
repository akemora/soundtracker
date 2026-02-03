import { getTranslations } from "next-intl/server";
import { Link } from "@/i18n/routing";
import { Button } from "@/components/ui/button";
import { LanguageSelector } from "./LanguageSelector";
import { ThemeToggle } from "@/components/ThemeToggle";

export async function Header() {
  const t = await getTranslations("nav");

  const navLinks = [
    { href: "/", label: t("home") },
    { href: "/composers", label: t("composers") },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <span className="font-display text-xl font-bold tracking-tight">
            SOUND<span className="text-accent">TRACKER</span>
          </span>
        </Link>

        {/* Navigation */}
        <nav className="hidden md:flex items-center gap-6">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm font-medium transition-colors hover:text-accent text-foreground"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <LanguageSelector />
          <Button variant="outline" size="sm" asChild className="hidden sm:flex">
            <Link href="/composers">{t("composers")}</Link>
          </Button>
        </div>
      </div>
    </header>
  );
}
