import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useState } from 'react';
import MainLayout from './layouts/MainLayout';
import MarketOverviewPage from './pages/MarketOverviewPage';
import StockAnalyzerPage from './pages/StockAnalyzerPage';
import ScreenerPage from './pages/ScreenerPage';
import ComparePage from './pages/ComparePage';

export default function App() {
  const [symbol, setSymbol] = useState('RELIANCE.NS'); // Default to Reliance
  
  return (
    <BrowserRouter>
      <MainLayout symbol={symbol} onSymbolChange={setSymbol}>
        <Routes>
          <Route path="/" element={<Navigate to="/market" replace />} />
          <Route path="/market" element={<MarketOverviewPage />} />
          <Route path="/stock/:symbol" element={<StockAnalyzerPage onSymbolChange={setSymbol} />} />
          <Route path="/screener" element={<ScreenerPage />} />
          <Route path="/compare" element={<ComparePage />} />
        </Routes>
      </MainLayout>
    </BrowserRouter>
  );
}
