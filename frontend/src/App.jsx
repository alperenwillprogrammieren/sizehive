import { NavLink, Route, Routes } from "react-router-dom";
import "./App.css";
import { useWatchlist } from "./collections";
import ThemeToggle from "./components/ThemeToggle";
import SearchPage from "./pages/SearchPage";
import ProductDetailPage from "./pages/ProductDetailPage";
import DashboardPage from "./pages/DashboardPage";
import DealsPage from "./pages/DealsPage";
import WatchlistPage from "./pages/WatchlistPage";

function App() {
  const watchlist = useWatchlist();

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
              {watchlist.length > 0 && <span className="nav-badge">{watchlist.length}</span>}
            </NavLink>
            <NavLink to="/dashboard">Dashboard</NavLink>
          </nav>
          <ThemeToggle />
        </div>
      </header>

      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/product/:variantId" element={<ProductDetailPage />} />
        <Route path="/deals" element={<DealsPage />} />
        <Route path="/merkliste" element={<WatchlistPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
      </Routes>
    </div>
  );
}

export default App;
