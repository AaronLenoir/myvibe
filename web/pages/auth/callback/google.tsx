import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function GoogleCallback() {
  const router = useRouter();

  useEffect(() => {
    const hash = window.location.hash.substring(1);
    const params = new URLSearchParams(hash);
    const accessToken = params.get('access_token');

    if (accessToken) {
      // Call our API to exchange Google token for our JWT
      fetch('http://localhost:8000/auth/google', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token: accessToken }),
      })
        .then((res) => res.json())
        .then((data) => {
          localStorage.setItem('token', data.access_token);
          localStorage.setItem('user', JSON.stringify(data.user));
          router.push('/dashboard');
        })
        .catch((error) => {
          console.error('Login failed:', error);
          router.push('/login?error=1');
        });
    } else {
      router.push('/login?error=1');
    }
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      <p className="ml-4">Authenticating...</p>
    </div>
  );
}
