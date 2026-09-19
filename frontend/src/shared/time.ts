// Clock formatting shared by the panel and the card.
//
// Both draw the same walk-test banner from the same status payload (§11.3),
// so both format the same countdown; a second copy of this would be a banner
// that disagreed with itself between a dashboard and the panel.

/** m:ss, for a countdown measured in minutes rather than in seconds. */
export function mmss(seconds: number): string {
  const whole = Math.max(0, Math.round(seconds));
  return `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, "0")}`;
}

/** Seconds left until `iso`, never negative. `offset` is the server clock
 * minus the browser's, which both the panel and the card already track. */
export function secondsUntil(iso: string, offset = 0): number {
  return Math.max(0, Math.round((Date.parse(iso) - (Date.now() + offset)) / 1000));
}
