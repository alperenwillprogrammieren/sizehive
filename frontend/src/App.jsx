import { NavLink, Route, Routes } from "react-router-dom";
import "./App.css";
import { useAuth } from "./authContext";
import ThemeToggle from "./components/ThemeToggle";
import CompareBar from "./components/CompareBar";
import AccountPage from "./pages/AccountPage";
import SearchPage from "./pages/SearchPage";
import ProductDetailPage from "./pages/ProductDetailPage";
import ComparePage from "./pages/ComparePage";
import DashboardPage from "./pages/DashboardPage";
import DealsPage from "./pages/DealsPage";
import LoginPage from "./pages/LoginPage";
import WatchlistPage from "./pages/WatchlistPage";
import { useWatchlist } from "./watchlistContext";
import { useCompareList } from "./collections";

function App() {
  const { entries } = useWatchlist();
  const { user } = useAuth();
  const compareList = useCompareList();

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>sizehive</h1>
          <p className="tagline">Kleidung, shopübergreifend gefiltert</p>
        </div>
        <div className="app-header-right">
          <nav className="app-nav">
            <NavLink to="/" end>
              Suche
            </NavLink>
            <NavLink to="/deals">Deals</NavLink>
            <NavLink to="/merkliste">
              Merkliste
              {entries.length > 0 && <span className="nav-badge">{entries.length}</span>}
            </NavLink>
            <NavLink to="/vergleich">
              Vergleich
              {compareList.length > 0 && <span className="nav-badge">{compareList.length}</span>}
            </NavLink>
            <NavLink to="/dashboard">Dashboard</NavLink>
            {user ? (
              <NavLink to="/konto" title={user.email}>
                Konto
              </NavLink>
            ) : (
              <NavLink to="/login">Anmelden</NavLink>
            )}
          </nav>
          <ThemeToggle />
        </div>
      </header>

      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/product/:variantId" element={<ProductDetailPage />} />
        <Route path="/deals" element={<DealsPage />} />
        <Route path="/merkliste" element={<WatchlistPage />} />
        <Route path="/vergleich" element={<ComparePage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/konto" element={<AccountPage />} />
      </Routes>

      <CompareBar />
    </div>
  );
}

export default App;
