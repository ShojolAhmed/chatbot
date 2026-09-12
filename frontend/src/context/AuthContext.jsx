import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { authApi } from '../services/authApi'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [status, setStatus] = useState('loading') // 'loading' | 'signed-out' | 'signed-in'
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [signInError, setSignInError] = useState(null)

  useEffect(() => {
    const controller = new AbortController()
    authApi
      .getSession({ signal: controller.signal })
      .then((sessionUser) => {
        setUser(sessionUser)
        setStatus(sessionUser ? 'signed-in' : 'signed-out')
      })
      .catch(() => setStatus('signed-out'))
    return () => controller.abort()
  }, [])

  const openSignIn = useCallback(() => {
    setSignInError(null)
    setIsModalOpen(true)
  }, [])

  const closeSignIn = useCallback(() => setIsModalOpen(false), [])

  const signInWithGoogle = useCallback(() => {
    setSignInError(null)
    try {
      authApi.signInWithGoogle()
    } catch (err) {
      setSignInError(err?.message || 'Sign in is not available yet.')
    }
  }, [])

  const signOut = useCallback(async () => {
    await authApi.signOut()
    setUser(null)
    setStatus('signed-out')
  }, [])

  const value = useMemo(
    () => ({
      user,
      status,
      isSignedIn: status === 'signed-in',
      isModalOpen,
      signInError,
      openSignIn,
      closeSignIn,
      signInWithGoogle,
      signOut,
    }),
    [user, status, isModalOpen, signInError, openSignIn, closeSignIn, signInWithGoogle, signOut],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}
