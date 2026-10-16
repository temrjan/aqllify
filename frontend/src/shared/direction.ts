export type Direction = 'ru' | 'uz';

export function directionFromPath(pathname: string): Direction | null {
  if (pathname === '/ru' || pathname.startsWith('/ru/')) return 'ru';
  if (pathname === '/uz' || pathname.startsWith('/uz/')) return 'uz';
  return null;
}
