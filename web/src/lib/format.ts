/** Norwegian thousands separator: a non-breaking space, per the handoff. */
export function formatNb(n: number): string {
  return n.toLocaleString("nb-NO").replace(/\s/g, "\u00a0");
}
