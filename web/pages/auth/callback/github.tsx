import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function GithubCallback() {
  const router = useRouter();
  const { code, state } = router.query;

  useEffect(() => {
    if (code) {
      // Call our API to exchange GitHub code for JWT
      fetch('http://localhost:8000/auth/github', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code: code as string }),
      })
        .then((res) => res.json())
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
