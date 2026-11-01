import { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import axios from 'axios'

export default function Dashboard() {
  const router = useRouter()
  const [user, setUser] = useState<{name: string, email: string, avatar: string} | null>(null)

  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem('token')
      if (!token) {
        router.push('/login')
        return
      }

      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        const response = await axios.get(`${apiUrl}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        setUser(response.data)
      } catch (err) {
        console.error('Failed to fetch user:', err)
        router.push('/login')
      }
    }

    fetchUser()
  }, [router])

  if (!user) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Dashboard</h1>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <p className="text-lg">Welcome to Roster App!</p>
        </div>
      </div>
    </div>
  )
}
