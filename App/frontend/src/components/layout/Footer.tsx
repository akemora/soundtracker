"use client";

import { useTranslations } from "next-intl";
import { Link } from "@/i18n/routing";
import { Separator } from "@/components/ui/separator";

export function Footer() {
  const t = useTranslations("footer");
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-border bg-muted/30">
      <div className="container py-8 md:py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Brand */}
          <div className="space-y-4">
            <Link href="/" className="flex items-center gap-2">
              <span className="font-display text-lg font-bold tracking-tight">
                SOUND<span className="text-accent">TRACKER</span>
              </span>
            </Link>
            <p className="text-sm text-muted-foreground max-w-xs">
              {t("description")}
            </p>
          </div>

          {/* Links */}
          <div className="space-y-4">
            <h4 className="font-medium">Enlaces</h4>
            <nav className="flex flex-col gap-2">
              <Link
                href="/"
                className="text-sm text-muted-foreground hover:text-accent transition-colors"
              >
                Inicio
              </Link>
              <Link
                href="/composers"
                className="text-sm text-muted-foreground hover:text-accent transition-colors"
              >
                Compositores
              </Link>
            </nav>
          </div>

          {/* Info */}
          <div className="space-y-4">
            <h4 className="font-medium">Proyecto</h4>
            <p className="text-sm text-muted-foreground">
              Enciclopedia de compositores de bandas sonoras del cine.
            </p>
          </div>
        </div>

        <Separator className="my-8" />

        <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
          <p className="text-xs text-muted-foreground">
            &copy; {currentYear} SOUNDTRACKER. {t("rights")}.
          </p>
        </div>
      </div>
    </footer>
  );
}
