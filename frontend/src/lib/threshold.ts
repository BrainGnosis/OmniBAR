const STORAGE_KEY = 'omnibar-threshold';
const DEFAULT_THRESHOLD = 0.7;

export function getStoredThreshold(defaultValue: number = DEFAULT_THRESHOLD): number {
  if (typeof window === 'undefined') {
    return defaultValue;
  }
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      return defaultValue;
    }
    const value = Number(stored);
    if (!Number.isFinite(value) || value <= 0 || value > 1) {
      return defaultValue;
    }
    return value;
  } catch (error) {
    console.warn('Failed to read threshold from localStorage', error);
    return defaultValue;
  }
}

export function setStoredThreshold(value: number): void {
  if (typeof window === 'undefined') {
    return;
  }
  try {
    window.localStorage.setItem(STORAGE_KEY, value.toString());
  } catch (error) {
    console.warn('Failed to persist threshold to localStorage', error);
  }
}

export function getDefaultThreshold(): number {
  return DEFAULT_THRESHOLD;
}
