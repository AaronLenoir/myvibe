import { useEffect } from 'react'
import { useRouter } from 'next/router'
import axios from 'axios'

export default function GitHubCallback() {
  const router = useRouter()
  const { code, error } = router.query

  useEffect(() => {
    const fetchToken = async () => {
      if (error) {
        router.push('/login?error=1')
        return
      }

      if (code && typeof code === 'string') {
        try {
          const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
          const response = await axios.post(`${apiUrl}/auth/github`, { code })
          
          if (response.data.token) {
            localStorage.setItem('token', response.data.token)
            router.push('/dashboard')
          } else {
            router.push('/login?error=1')
          }
        } catch (err) {
          console.error('GitHub OAuth error:', err)
          router.push('/login?error=1')
        }
      }
    }

    if (router.isReady) {
      fetchToken()
    }
  }, [code, error, router])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <p>Authenticating with GitHub...</p>
      </div>
    </div>
  )
}
