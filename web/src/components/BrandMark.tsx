// The mockup's brand mark: two dashed orbit rings around a red core
// (UI-WIP/drydocs-landing-dark.html). Red = brand core (site-plan §2 brand
// rule: red is brand core + alert only — this is the "core" use).
export default function BrandMark({ size = 26 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 26 26" aria-hidden="true">
      <circle cx="13" cy="13" r="10" fill="none" stroke="#2E6BC4" strokeWidth="2.4" strokeDasharray="18 8" />
      <circle cx="13" cy="13" r="10" fill="none" stroke="#D9B831" strokeWidth="2.4" strokeDasharray="10 38" strokeDashoffset="-20" />
      <circle cx="13" cy="13" r="4" fill="#C8202E" />
    </svg>
  )
}
