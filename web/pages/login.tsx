import { useEffect } from 'react'
import { useRouter } from 'next/router'

export default function Login() {
  const router = useRouter()
  const githubClientId = process.env.NEXT_PUBLIC_GITHUB_CLIENT_ID || ''

  const handleGitHubLogin = () => {
    const redirectUri = encodeURIComponent('https://roster.aaronlenoir.com/auth/callback/github')
    const githubAuthUrl = `https://github.com/login/oauth/authorize?client_id=${githubClientId}&redirect_uri=${redirectUri}&scope=user:email`
    window.location.href = githubAuthUrl
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-8 rounded-lg shadow-md w-96">
        <h1 className="text-2xl font-bold text-center mb-6">Roster App</h1>
        <button
          onClick={handleGitHubLogin}
          className="w-full bg-black text-white py-2 px-4 rounded hover:bg-gray-800 transition-colors"
        >
          Continue with GitHub
        </button>
      </div>
    </div>
  )
}
