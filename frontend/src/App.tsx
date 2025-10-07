import { useState } from 'react';

import AppShell, { AppRoute } from './AppShell';
import ControlRoom from './pages/ControlRoom';
import Benchmarks from './pages/Benchmarks';
import Runs from './pages/Runs';
import DocumentExtraction from './pages/DocumentExtraction';
import LatteLab from './pages/LatteLab';

export default function App() {
  const [route, setRoute] = useState<AppRoute>('control');

  const renderPage = () => {
    switch (route) {
      case 'benchmarks':
        return <Benchmarks />;
      case 'runs':
        return <Runs />;
      case 'documents':
        return <DocumentExtraction />;
      case 'latte':
        return <LatteLab />;
      case 'control':
      default:
        return <ControlRoom />;
    }
  };

  return (
    <AppShell route={route} onNavigate={setRoute}>
      {renderPage()}
    </AppShell>
  );
}
