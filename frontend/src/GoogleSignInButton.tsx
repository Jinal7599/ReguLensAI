import { useEffect, useRef, useState } from "react";
import { api } from "./api";

type GoogleCredentialResponse = { credential?: string };
type GoogleIdApi = {
  initialize: (options: { client_id: string; nonce?: string; callback: (response: GoogleCredentialResponse) => void }) => void;
  renderButton: (element: HTMLElement, options: Record<string, string | number | boolean>) => void;
  disableAutoSelect: () => void;
};

declare global {
  interface Window {
    google?: { accounts: { id: GoogleIdApi } };
  }
}

interface GoogleSignInButtonProps {
  onCredential: (credential: string) => void;
  disabled?: boolean;
}

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID ?? "";

export default function GoogleSignInButton({ onCredential, disabled = false }: GoogleSignInButtonProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const callbackRef = useRef(onCredential);
  const [error, setError] = useState("");

  useEffect(() => {
    callbackRef.current = onCredential;
  }, [onCredential]);

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) {
      setError("Google sign-in is not configured. Set VITE_GOOGLE_CLIENT_ID on the frontend service.");
      return;
    }

    let cancelled = false;
    let script = document.querySelector<HTMLScriptElement>("script[data-google-identity]");
    const initialize = async () => {
      if (cancelled || !hostRef.current || !window.google?.accounts.id) return;
      try {
        const { nonce } = await api.oauthNonce();
        if (cancelled || !hostRef.current || !window.google?.accounts.id) return;
        const googleId = window.google.accounts.id;
        googleId.initialize({
          client_id: GOOGLE_CLIENT_ID,
          nonce,
          callback: (response) => {
            if (response.credential) callbackRef.current(response.credential);
            else setError("Google did not return a sign-in credential. Please try again.");
          },
        });
        hostRef.current.replaceChildren();
        googleId.renderButton(hostRef.current, {
        theme: "outline",
        size: "large",
        shape: "rectangular",
        text: "continue_with",
        width: 280,
          logo_alignment: "left",
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to prepare secure Google sign-in.");
      }
    };

    if (!script) {
      script = document.createElement("script");
      script.src = "https://accounts.google.com/gsi/client";
      script.async = true;
      script.defer = true;
      script.dataset.googleIdentity = "true";
      script.addEventListener("load", initialize);
      script.addEventListener("error", () => setError("Google sign-in could not be loaded. Check browser network or content-blocking settings."));
      document.head.appendChild(script);
    } else if (window.google?.accounts.id) {
      initialize();
    } else {
      script.addEventListener("load", initialize);
    }

    return () => {
      cancelled = true;
      script?.removeEventListener("load", initialize);
    };
  }, []);

  return <div className="google-signin-wrap">
    <div ref={hostRef} aria-label="Sign in with Google" />
    {disabled && <div className="auth-button-overlay" />}
    {error && <p className="auth-inline-error" role="alert">{error}</p>}
  </div>;
}
