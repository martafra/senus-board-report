/**
 * A section's page heading with a small colored identity dot beside it. The color marks identity
 * (which section this is) so it doesn't need to go on the text itself, keeping the heading in the
 * normal text color for readability/contrast.
 */
export function SectionHeading({ color, children }: { color: string; children: string }) {
  return (
    <h2 className="flex items-center gap-2 text-xl font-semibold">
      <span className="inline-block size-2.5 rounded-full" style={{ backgroundColor: color }} />
      {children}
    </h2>
  )
}
