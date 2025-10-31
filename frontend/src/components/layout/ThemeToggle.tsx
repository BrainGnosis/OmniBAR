import { useEffect, useState } from 'react';
import { Moon, Sun } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { useThemePreference } from '@/hooks/useThemePreference';

type ThemeToggleProps = {
  className?: string;
};

export function ThemeToggle({ className }: ThemeToggleProps) {
  const { isDark, toggleTheme } = useThemePreference();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  const Icon = isDark ? Sun : Moon;
  const label = isDark ? 'Switch to light mode' : 'Switch to dark mode';

  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      className={className}
      onClick={toggleTheme}
      aria-label={label}
      title={label}
    >
      <Icon className="h-4 w-4" />
      <span className="hidden sm:inline">{isDark ? 'Light mode' : 'Dark mode'}</span>
    </Button>
  );
}
