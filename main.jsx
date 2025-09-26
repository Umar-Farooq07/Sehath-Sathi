import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { Auth0Provider } from '@auth0/auth0-react';
import './index.css';
import App from './App.jsx';

// --- Auth0 Configuration ---
// IMPORTANT: Replace these placeholder values with your actual Auth0 credentials
// You can get these from your Auth0 Application settings page.
const auth0Domain = "YOUR_AUTH0_DOMAIN"; // e.g., "dev-12345.us.auth0.com"
const auth0ClientId = "YOUR_AUTH0_CLIENT_ID";

createRoot(document.getElementById('root')).render(
  <StrictMode>
    {/* The Auth0Provider component makes authentication state and methods 
      (like loginWithRedirect, logout, user, isAuthenticated) 
      available to every component in your application.
    */}
    <Auth0Provider
      domain={auth0Domain}
      clientId={auth0ClientId}
      authorizationParams={{
        redirect_uri: window.location.origin
      }}
    >
      <App />
    </Auth0Provider>
  </StrictMode>,
);
