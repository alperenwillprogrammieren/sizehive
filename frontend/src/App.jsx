import { NavLink, Route, Routes } from "react-router-dom";
import "./App.css";
import SearchPage from "./pages/SearchPage";
import ProductDetailPage from "./pages/ProductDetailPage";
import DashboardPage from "./pages/DashboardPage";

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>sizehive</h1>
          <p className="tagline">Kleidung, shopübergreifend gefiltert</p>
        </div>
        <nav className="app-nav">
          <NavLink to="/" end>
            Suche
          </NavLink>
          <NavLink to="/dashboard">Dashboard</NavLink>
        </nav>
      </header>

      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/product/:variantId" element={<ProductDetailPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
      </Routes>
    </div>
  );
}

export default App;
