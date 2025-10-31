import { useState } from 'react';

import AppShell, { AppRoute } from './AppShell';
import ControlRoom from './pages/ControlRoom';
import Benchmarks from './pages/Benchmarks';
import Runs from './pages/Runs';
import DocumentExtraction from './pages/DocumentExtraction';
import OmniBrew from './pages/OmniBrew';
import Chat from './pages/Chat';

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
        return <OmniBrew />;
      case 'chat':
        return <Chat />;
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
