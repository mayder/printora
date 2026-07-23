export function nextAuthGeneration(current: number): number {
  return current + 1;
}

export function isCurrentAuthGeneration(current: number, captured: number): boolean {
  return current === captured;
}
