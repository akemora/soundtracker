"use client";

import { useLocale } from "next-intl";
import { usePathname, useRouter } from "@/i18n/routing";
import { Button } from "@/components/ui/button";
import { localeNames, type Locale } from "@/i18n/config";

export function LanguageSelector() {
  const locale = useLocale() as Locale;
  const router = useRouter();
  const pathname = usePathname();

  const toggleLocale = () => {
    const newLocale = locale === "es" ? "en" : "es";
    router.replace(pathname, { locale: newLocale });
  };

  const otherLocale = locale === "es" ? "en" : "es";

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={toggleLocale}
      className="text-sm font-medium"
      title={`Switch to ${localeNames[otherLocale]}`}
    >
      {locale.toUpperCase()}
    </Button>
  );
}
