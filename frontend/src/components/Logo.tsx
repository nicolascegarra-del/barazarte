import Link from "next/link";

/** Logotipo BarazArte: "Baraz" en serif y "Arte" en cursiva dorada. */
export function Logo({ className = "text-3xl" }: { className?: string }) {
  return (
    <Link href="/" aria-label="BarazArte, inicio" className={`font-serif font-medium tracking-wide ${className}`}>
      Baraz<i className="font-normal text-gold">Arte</i>
    </Link>
  );
}
