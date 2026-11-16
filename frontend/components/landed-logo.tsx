/* eslint-disable @next/next/no-img-element -- these are small SVG files; plain <img> keeps their animation playing. */
import { cn } from "@/lib/utils";

// The Landed logos. The files live in public/brand and come from docs/brand
// (run `python scripts/make_brand_svgs.py` after the logos there change).
//
// The animated versions play once each time they load: the plane flies in and lands.
// Every logo has a thin white outline where the plane's path crosses the letters,
// so place them on white, or use tone="dark" on the night blue (bg-brand-950).

type LogoProps = { className?: string; animated?: boolean };
type WordmarkProps = LogoProps & {
  /** "dark" = the version drawn for the night-blue (brand-950) sidebar and landing panel. Always animated. */
  tone?: "light" | "dark";
};

/** The full word "Landed" with the plane landed on the final d. */
export function LandedWordmark({ className, animated = false, tone = "light" }: WordmarkProps) {
  const src = tone === "dark"
    ? "/brand/landed-wordmark-animated-dark.svg"
    : animated ? "/brand/landed-wordmark-animated.svg" : "/brand/landed-wordmark-logo.svg";
  return (
    <img
      alt="Landed"
      className={cn("block h-auto select-none", className)}
      draggable={false}
      src={src}
    />
  );
}

/** The square "L" mark with the plane circling it. Good for small spaces. */
export function LandedMark({ className, animated = false }: LogoProps) {
  return (
    <img
      alt="Landed"
      className={cn("block h-auto select-none", className)}
      draggable={false}
      src={animated ? "/brand/landed-logo-animated.svg" : "/brand/landed-icon.svg"}
    />
  );
}
