import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';

declare const window: any;

export default function Login() {
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleGithubLogin = () => {
    setIsLoading(true);
    
    const githubClientId = process.env.NEXT_PUBLIC_GITHUB_CLIENT_ID || '';
    const redirectUri = typeof window !== 'undefined' 
      ? window.location.origin + '/auth/callback/github' 
      : 'http://localhost:3000/auth/callback/github';
    
    const url = `https://github.com/login/oauth/authorize?` +
      `client_id=${githubClientId}&` +
      `redirect_uri=${encodeURIComponent(redirectUri)}&` +
      `scope=user:email&` +
      `state=github`;

    window.location.href = url;
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold">Welcome to Roster</h1>
          <p className="text-gray-600 mt-2">Sign in with your GitHub account</p>
        </div>

        <div className="space-y-4">
          <button
            onClick={handleGithubLogin}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-3 px-6 py-3 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors disabled:opacity-50"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C5.374 0 0 5.373 0 12 0 17.942 4.988 21.785 11.485 21.998c.005.001.008.001.012.001.007 0 .012-.002.017-.003.01-.004.019-.008.028-.013.04-.02.079-.04.116-.063.08-.05 1.835-1.222 1.835-2.518 0-1.015-.01-1.835-.01-2.463-.01-.55.07-1.22.21-1.71-.96-.28-2.04-.31-3.1-.11-.8.14-1.6.5-2.2.9-.5-.3-1.1-.5-1.6-.5-1.1 0-2.3.3-3.3.9-.8.5-1.6 1.1-2.3 1.8-.6.6-1.2 1.3-1.6 2.1-.4.8-.6 1.7-.6 2.7 0 .8.1 1.6.2 2.4.1.7.3 1.5.5 2.2.3.8.7 1.6 1.1 2.3.5.8 1.1 1.5 1.7 2.1.8.8 1.7 1.5 2.7 2.1.6.3 1.2.5 1.8.6.9.2 1.9.3 3 .3.8 0 1.6-.2 2.4-.5.8-.3 1.6-.8 2.3-1.4.6-.5 1.2-1.1 1.7-1.8.7-.8 1.3-1.7 1.8-2.7.5-1 .8-2 .8-3.1 0-.8-.1-1.6-.2-2.4-.1-.8-.3-1.5-.6-2.2-.2-.6-.5-1.2-.9-1.7-.4-.5-.9-.9-1.5-1.2-.8-.4-1.7-.6-2.6-.6-.8 0-1.6.1-2.4.4-.8.2-1.6.6-2.3 1.2-.6.5-1.1 1.2-1.5 2-.4.8-.7 1.7-.7 2.7z"/>
            </svg>
            <span>Continue with GitHub</span>
          </button>
        </div>
      </div>
    </div>
  );
}
