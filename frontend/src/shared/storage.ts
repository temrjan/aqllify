export function readLocal(key: string): string | null {
  try { return localStorage.getItem(key); } catch { return null; }
}
export function writeLocal(key: string, value: string): void {
  try { localStorage.setItem(key, value); } catch { /* Storage is optional; server state remains authoritative. */ }
}
export function removeLocal(key: string): void {
  try { localStorage.removeItem(key); } catch { /* Storage is optional; navigation remains available. */ }
}
