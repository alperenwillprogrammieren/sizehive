import { createContext, useContext } from "react";

// Context and hook live apart from the provider component so that
// auth.jsx exports a component and nothing else — otherwise React Fast
// Refresh can't hot-reload the provider.
export const AuthContext = createContext({
  user: null,
  loading: true,
  refresh: () => {},
  signOut: () => {},
});

export function useAuth() {
  return useContext(AuthContext);
}
