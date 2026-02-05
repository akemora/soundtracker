# CONVENTIONS_FRONTEND.md - SOUNDTRACKER

**Estándares de Frontend: CSS, HTML y JavaScript** | v1.0 | 2026-02-03

> Este documento es **de solo lectura para agentes IA** (usar como contexto, no modificar).
> Para estándares backend/Python, ver `CONVENTIONS.md`.
> Para gobernanza operativa, ver `AGENTS.md`.

---

## 0. Alcance

Este documento define **estándares de código frontend** para SOUNDTRACKER:
- CSS/Tailwind: Arquitectura de estilos, design tokens
- HTML: Semántica, accesibilidad (a11y)
- TypeScript: Componentes React/Next.js, hooks
- Responsive design: Mobile-first approach
- Theming: Dark mode, CSS variables

**Stack Frontend**:
- Next.js 14 (App Router)
- TypeScript 5.x
- Tailwind CSS 3.x
- shadcn/ui components
- next-intl (i18n)

---

## 1. Arquitectura de Estilos (CRÍTICO)

### 1.1 Regla de Oro: Tailwind + Design Tokens

**✅ OBLIGATORIO**:
- Usar Tailwind CSS con configuración de tokens
- Centralizar colores, spacing, fonts en `tailwind.config.ts`
- Usar componentes de shadcn/ui como base
- Mantener consistencia con el sistema de diseño

**❌ PROHIBIDO**:
```tsx
// ❌ CSS inline repetido (anti-pattern)
<button style={{
  backgroundColor: '#C96A40',
  color: 'white',
  padding: '8px 16px',
}}>
  Click
</button>
```

**✅ CORRECTO**:
```tsx
// ✅ Tailwind con tokens configurados
<button className="bg-primary-500 text-white px-4 py-2 rounded-md hover:bg-primary-600 transition-colors">
  Click
</button>
```

---

## 2. Design Tokens (Tailwind Config)

### 2.1 Paleta de Colores

```typescript
// tailwind.config.ts
const config: Config = {
  theme: {
    extend: {
      colors: {
        // Paleta principal (cálida, cinematográfica)
        primary: {
          50: "#FDF8F6",
          100: "#F9EBE5",
          200: "#F3D5C8",
          300: "#E9B59D",
          400: "#D98B66",
          500: "#C96A40",  // Principal
          600: "#A85532",
          700: "#8A4428",
          800: "#6D3620",
          900: "#4A2515",
        },
        secondary: {
          50: "#F5F7FA",
          100: "#E4E9F0",
          200: "#C9D3E1",
          300: "#A3B3CA",
          400: "#7A91B0",
          500: "#5A7499",  // Secundario
          600: "#485D7A",
          700: "#3A4A61",
          800: "#2D3A4D",
          900: "#1F2937",
        },
        // Acentos para premios
        accent: {
          gold: "#D4AF37",      // Oscar/premios
          silver: "#C0C0C0",    // Nominaciones
          bronze: "#CD7F32",    // Menciones
        },
        // Backgrounds
        background: {
          light: "#FAFAF9",
          dark: "#1A1A1A",
        },
      },
    },
  },
};
```

### 2.2 Tipografía

```typescript
// tailwind.config.ts
fontFamily: {
  sans: ["var(--font-inter)", "system-ui", "sans-serif"],
  display: ["var(--font-playfair)", "Georgia", "serif"],  // Para títulos
  mono: ["var(--font-fira-code)", "monospace"],
},
fontSize: {
  xs: ["0.75rem", { lineHeight: "1rem" }],
  sm: ["0.875rem", { lineHeight: "1.25rem" }],
  base: ["1rem", { lineHeight: "1.5rem" }],
  lg: ["1.125rem", { lineHeight: "1.75rem" }],
  xl: ["1.25rem", { lineHeight: "1.75rem" }],
  "2xl": ["1.5rem", { lineHeight: "2rem" }],
  "3xl": ["1.875rem", { lineHeight: "2.25rem" }],
  "4xl": ["2.25rem", { lineHeight: "2.5rem" }],
},
```

### 2.3 Spacing y Shadows

```typescript
// tailwind.config.ts
spacing: {
  "18": "4.5rem",
  "88": "22rem",
  "128": "32rem",
},
borderRadius: {
  "4xl": "2rem",
},
boxShadow: {
  "poster": "0 4px 20px -2px rgba(0, 0, 0, 0.3)",
  "card": "0 2px 8px -1px rgba(0, 0, 0, 0.1)",
  "card-hover": "0 8px 24px -4px rgba(0, 0, 0, 0.15)",
},
```

---

## 3. Estructura de Archivos

```
frontend/
├── src/
│   ├── app/
│   │   ├── [locale]/
│   │   │   ├── layout.tsx           # Layout con providers
│   │   │   ├── page.tsx             # Home
│   │   │   ├── composers/
│   │   │   │   ├── page.tsx         # Listado
│   │   │   │   └── [slug]/
│   │   │   │       └── page.tsx     # Detalle
│   │   │   └── search/
│   │   │       └── page.tsx         # Búsqueda
│   │   └── api/                     # API routes
│   ├── components/
│   │   ├── ui/                      # shadcn/ui (no modificar)
│   │   ├── layout/                  # Header, Footer, Sidebar
│   │   ├── composers/               # Componentes de compositor
│   │   │   ├── ComposerCard.tsx
│   │   │   ├── ComposerGrid.tsx
│   │   │   ├── ComposerDetail.tsx
│   │   │   ├── Top10Gallery.tsx
│   │   │   └── FilmographyList.tsx
│   │   └── search/                  # Componentes de búsqueda
│   │       ├── SearchBar.tsx
│   │       └── SearchResults.tsx
│   ├── lib/
│   │   ├── api.ts                   # API client
│   │   ├── types.ts                 # TypeScript types
│   │   └── utils.ts                 # Helpers (cn, etc.)
│   ├── styles/
│   │   └── globals.css              # Tailwind directives
│   └── i18n/
│       ├── messages/
│       │   ├── es.json
│       │   └── en.json
│       └── config.ts
├── public/
│   └── assets/                      # Symlink a outputs
├── tailwind.config.ts
└── next.config.js
```

---

## 4. Componentes React (TypeScript)

### 4.1 Estructura de Componente

```tsx
// components/composers/ComposerCard.tsx
import Image from "next/image";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { ComposerSummary } from "@/lib/types";

interface ComposerCardProps {
  composer: ComposerSummary;
  className?: string;
}

export function ComposerCard({ composer, className }: ComposerCardProps) {
  const { name, slug, photoPath, filmCount, wins, careerStart, careerEnd } = composer;

  return (
    <Link href={`/composers/${slug}`} className={cn("group", className)}>
      <article className="bg-white rounded-xl shadow-card hover:shadow-card-hover transition-shadow duration-300 overflow-hidden">
        {/* Contenido */}
      </article>
    </Link>
  );
}
```

### 4.2 Props Interface

**✅ CORRECTO**:
```tsx
// Props tipadas con interface
interface ButtonProps {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md" | "lg";
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
}

export function Button({
  variant = "primary",
  size = "md",
  children,
  onClick,
  disabled = false,
  className,
}: ButtonProps) {
  // ...
}
```

**❌ INCORRECTO**:
```tsx
// Sin tipos
export function Button(props) {
  return <button style={{ background: "blue" }}>{props.children}</button>;
}
```

### 4.3 Hooks Personalizados

```tsx
// hooks/useComposer.ts
import useSWR from "swr";
import type { ComposerDetail } from "@/lib/types";

interface UseComposerOptions {
  slug: string;
}

interface UseComposerReturn {
  composer: ComposerDetail | undefined;
  isLoading: boolean;
  error: Error | undefined;
}

export function useComposer({ slug }: UseComposerOptions): UseComposerReturn {
  const { data, error, isLoading } = useSWR<ComposerDetail>(
    `/api/composers/${slug}`,
    fetcher
  );

  return {
    composer: data,
    isLoading,
    error,
  };
}
```

---

## 5. HTML Semántico y Accesibilidad

### 5.1 Etiquetas Semánticas

```tsx
// ✅ CORRECTO - HTML semántico
<header className="...">
  <nav aria-label="Navegación principal">
    <ul role="list">
      <li><Link href="/">Inicio</Link></li>
      <li><Link href="/composers">Compositores</Link></li>
    </ul>
  </nav>
</header>

<main id="main-content">
  <article aria-labelledby="composer-name">
    <h1 id="composer-name">{composer.name}</h1>
    <section aria-labelledby="biography-heading">
      <h2 id="biography-heading">Biografía</h2>
      <p>{composer.biography}</p>
    </section>
  </article>
</main>

<footer>
  <p>&copy; 2026 SOUNDTRACKER</p>
</footer>
```

```tsx
// ❌ INCORRECTO - Todo con divs
<div className="header">
  <div className="nav">
    <div className="list">
      <div className="item"><a href="/">Inicio</a></div>
    </div>
  </div>
</div>
```

### 5.2 Accesibilidad (a11y)

```tsx
// ✅ Con atributos de accesibilidad
<button
  aria-label="Cerrar modal"
  onClick={closeModal}
  className="p-2 rounded-full hover:bg-secondary-100"
>
  <XIcon className="w-5 h-5" aria-hidden="true" />
</button>

<Image
  src={composer.photoPath}
  alt={`Fotografía de ${composer.name}`}
  width={300}
  height={400}
/>

<form onSubmit={handleSubmit} aria-label="Formulario de búsqueda">
  <label htmlFor="search-input" className="sr-only">
    Buscar compositor
  </label>
  <input
    id="search-input"
    type="search"
    aria-describedby="search-hint"
    placeholder="John Williams..."
  />
  <p id="search-hint" className="text-sm text-secondary-500">
    Busca por nombre, película o premio
  </p>
</form>
```

---

## 6. Responsive Design (Mobile-First)

### 6.1 Breakpoints

```typescript
// tailwind.config.ts (defaults de Tailwind)
screens: {
  'sm': '640px',   // Mobile landscape
  'md': '768px',   // Tablet
  'lg': '1024px',  // Desktop
  'xl': '1280px',  // Large desktop
  '2xl': '1536px', // Extra large
}
```

### 6.2 Mobile-First Approach

```tsx
// ✅ Mobile first (base → desktop)
<div className="
  grid grid-cols-1        /* Mobile: 1 columna */
  sm:grid-cols-2          /* Tablet: 2 columnas */
  md:grid-cols-3          /* Desktop: 3 columnas */
  lg:grid-cols-4          /* Large: 4 columnas */
  gap-4 md:gap-6 lg:gap-8
">
  {composers.map((composer) => (
    <ComposerCard key={composer.id} composer={composer} />
  ))}
</div>
```

### 6.3 Contenedores Responsivos

```tsx
// Layout con contenedor responsivo
<div className="
  max-w-7xl mx-auto
  px-4 sm:px-6 lg:px-8
">
  {children}
</div>
```

---

## 7. Dark Mode

### 7.1 Configuración

```typescript
// tailwind.config.ts
module.exports = {
  darkMode: "class", // o "media"
  // ...
};
```

### 7.2 Uso en Componentes

```tsx
// Componente con soporte dark mode
<article className="
  bg-white dark:bg-secondary-900
  text-secondary-900 dark:text-secondary-100
  border border-secondary-200 dark:border-secondary-700
  shadow-card dark:shadow-none
">
  <h2 className="text-secondary-900 dark:text-white">
    {title}
  </h2>
  <p className="text-secondary-600 dark:text-secondary-300">
    {description}
  </p>
</article>
```

### 7.3 Toggle de Tema

```tsx
// components/ThemeToggle.tsx
"use client";

import { useTheme } from "next-themes";
import { Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      aria-label={theme === "dark" ? "Cambiar a modo claro" : "Cambiar a modo oscuro"}
    >
      <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
    </Button>
  );
}
```

---

## 8. Imágenes y Assets

### 8.1 next/image Optimization

```tsx
import Image from "next/image";

// ✅ Imagen optimizada
<Image
  src={`/api/assets/${posterPath}`}
  alt={`Póster de ${filmTitle}`}
  width={200}
  height={300}
  className="object-cover rounded-lg"
  placeholder="blur"
  blurDataURL="/placeholder-poster.jpg"
/>

// Para imágenes de tamaño dinámico
<div className="relative aspect-[2/3]">
  <Image
    src={posterPath}
    alt={filmTitle}
    fill
    sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
    className="object-cover"
  />
</div>
```

### 8.2 Lazy Loading

```tsx
import { lazy, Suspense } from "react";

// Lazy loading de componentes pesados
const FilmographyList = lazy(() => import("./FilmographyList"));

function ComposerDetail({ composer }) {
  return (
    <div>
      <Top10Gallery films={composer.top10} />

      <Suspense fallback={<FilmographySkeleton />}>
        <FilmographyList films={composer.filmography} />
      </Suspense>
    </div>
  );
}
```

---

## 9. i18n (Internacionalización)

### 9.1 Estructura de Mensajes

```json
// src/i18n/messages/es.json
{
  "home": {
    "title": "Enciclopedia de Compositores de Cine",
    "subtitle": "Descubre las mentes detrás de las bandas sonoras más memorables",
    "searchPlaceholder": "Buscar compositor, película o premio..."
  },
  "composer": {
    "biography": "Biografía",
    "style": "Estilo Musical",
    "top10": "Top 10 Bandas Sonoras",
    "filmography": "Filmografía Completa",
    "awards": "Premios y Nominaciones",
    "films": "{count, plural, one {# película} other {# películas}}",
    "wins": "{count, plural, one {# premio} other {# premios}}"
  },
  "common": {
    "loading": "Cargando...",
    "error": "Error al cargar datos",
    "retry": "Reintentar",
    "viewMore": "Ver más"
  }
}
```

### 9.2 Uso en Componentes

```tsx
// Usando next-intl
import { useTranslations } from "next-intl";

export function ComposerStats({ filmCount, wins }: Props) {
  const t = useTranslations("composer");

  return (
    <div>
      <span>{t("films", { count: filmCount })}</span>
      <span>{t("wins", { count: wins })}</span>
    </div>
  );
}
```

---

## 10. Performance

### 10.1 Memoización

```tsx
import { memo, useMemo, useCallback } from "react";

// Componente memoizado
export const ComposerCard = memo(function ComposerCard({ composer }: Props) {
  return <article>{/* ... */}</article>;
});

// useMemo para cálculos costosos
const filteredFilms = useMemo(() => {
  return films.filter((film) => film.year && film.year >= yearFrom);
}, [films, yearFrom]);

// useCallback para funciones pasadas como props
const handleSearch = useCallback((query: string) => {
  setSearchQuery(query);
}, []);
```

### 10.2 Loading States

```tsx
// Skeleton components
function ComposerCardSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="aspect-[3/4] bg-secondary-200 rounded-lg" />
      <div className="mt-4 h-4 bg-secondary-200 rounded w-3/4" />
      <div className="mt-2 h-3 bg-secondary-200 rounded w-1/2" />
    </div>
  );
}

// Uso con Suspense
<Suspense fallback={<ComposerCardSkeleton />}>
  <ComposerCard composer={composer} />
</Suspense>
```

---

## 11. Testing

### 11.1 React Testing Library

```tsx
// __tests__/ComposerCard.test.tsx
import { render, screen } from "@testing-library/react";
import { ComposerCard } from "@/components/composers/ComposerCard";

const mockComposer = {
  id: 1,
  name: "John Williams",
  slug: "john-williams",
  filmCount: 120,
  wins: 5,
};

describe("ComposerCard", () => {
  it("renders composer name", () => {
    render(<ComposerCard composer={mockComposer} />);
    expect(screen.getByText("John Williams")).toBeInTheDocument();
  });

  it("shows award badge when wins > 0", () => {
    render(<ComposerCard composer={mockComposer} />);
    expect(screen.getByText(/5.*Oscar/i)).toBeInTheDocument();
  });

  it("links to composer detail page", () => {
    render(<ComposerCard composer={mockComposer} />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/composers/john-williams");
  });
});
```

---

## 12. CSS Prohibido

❌ **NUNCA hacer**:

```css
/* ❌ !important */
.button { color: red !important; }

/* ❌ IDs para estilos */
#header { background: blue; }

/* ❌ Selectores muy específicos */
.container .sidebar .menu ul li a span { color: red; }

/* ❌ Magic numbers */
.card { padding: 13.5px; margin-top: 23px; }

/* ❌ Colores hardcodeados fuera de tokens */
.button { background: #3B82F6; }  /* Usar bg-primary-500 */
```

✅ **CORRECTO**:

```tsx
// Usar clases de Tailwind con tokens configurados
<button className="bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-md transition-colors">
  Click
</button>
```

---

## 13. Referencias Rápidas

### Comandos
```bash
npm run dev           # Desarrollo
npm run build         # Build producción
npm run lint          # ESLint
npm run type-check    # TypeScript
npm test              # Tests
```

### Enlaces
- [Next.js 14 Docs](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [shadcn/ui](https://ui.shadcn.com/)
- [next-intl](https://next-intl-docs.vercel.app/)
- [React Testing Library](https://testing-library.com/react)

---

**v1.0** | 2026-02-03 | SOUNDTRACKER | Para cambios: issue con tag `[CONVENTIONS]`
