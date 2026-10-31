import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function GithubCallback() {
  const router = useRouter();
  const { code } = router.query;

  useEffect(() => {
    if (code) {
      // Use the environment variable for API URL
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

      fetch(`${apiUrl}/auth/github`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code }),
      })
        .then((res) => {
          if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
          }
          return res.json();
        })
        .then((data) => {
          localStorage.setItem('token', data.access_token);
          localStorage.setItem('user', JSON.stringify(data.user));
          router.push('/dashboard');
        })
        .catch((error) => {
          console.error('GitHub login failed:', error);
          router.push('/login?error=1');
        });
    } else {
      router.push('/login?error=1');
    }
  }, [code, router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      <p className="ml-4">Authenticating with GitHub...</p>
    </div>
  );
}
