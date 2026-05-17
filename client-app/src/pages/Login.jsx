import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { login } from '../api'

export default function Login() {
  const [form, setForm] = useState({ username: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handle = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(form.username, form.password)
      navigate('/chat')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={s.page}>
      <div style={s.glow} />
      <div style={s.card}>
        <div style={s.iconWrap}>
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" fill="url(#g1)" />
            <defs>
              <linearGradient id="g1" x1="0" y1="0" x2="24" y2="24" gradientUnits="userSpaceOnUse">
                <stop stopColor="#a78bfa" />
                <stop offset="1" stopColor="#60a5fa" />
              </linearGradient>
            </defs>
          </svg>
        </div>
        <h1 style={s.title}>Welcome back</h1>
        <p style={s.subtitle}>Sign in to Secure Messenger</p>

        <form onSubmit={submit} style={s.form}>
          <div style={s.field}>
            <label style={s.label}>Username</label>
            <input style={s.input} name="username" placeholder="Enter your username" value={form.username} onChange={handle} required autoFocus />
          </div>
          <div style={s.field}>
            <label style={s.label}>Password</label>
            <input style={s.input} name="password" type="password" placeholder="Enter your password" value={form.password} onChange={handle} required />
          </div>
          {error && <div style={s.errorBox}>⚠️ {error}</div>}
          <button style={{ ...s.btn, opacity: loading ? 0.75 : 1 }} type="submit" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In →'}
          </button>
        </form>

        <p style={s.footer}>
          Don't have an account?{' '}
          <Link to="/register" style={s.link}>Create one</Link>
        </p>
      </div>
    </div>
  )
}

const s = {
  page: {
    minHeight: '100vh',
    background: 'linear-gradient(180deg, #f7fbff 0%, #f3f7fb 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontFamily: "Inter, 'Segoe UI', sans-serif",
    padding: 16,
    position: 'relative',
    overflow: 'hidden',
  },
  glow: {
    position: 'absolute',
    width: 420,
    height: 420,
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(124,58,237,0.16) 0%, rgba(6,182,212,0.08) 50%, transparent 70%)',
    top: '25%',
    left: '12%',
    transform: 'translate(-10%, -10%)',
    pointerEvents: 'none',
  },
  card: {
    background: 'linear-gradient(180deg, rgba(255,255,255,0.9), rgba(251,253,255,0.95))',
    borderRadius: 20,
    padding: '36px 34px',
    width: '100%',
    maxWidth: 440,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    boxShadow: '0 18px 50px rgba(2,6,23,0.08)',
    position: 'relative',
    zIndex: 1,
    border: '1px solid rgba(15,23,42,0.04)'
  },
  iconWrap: {
    width: 64,
    height: 64,
    borderRadius: 14,
    background: 'linear-gradient(135deg,#ff7ab6,#7c3aed)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 18,
    boxShadow: '0 10px 30px rgba(124,58,237,0.14)'
  },
  title: { margin: '0 0 6px', fontSize: 24, fontWeight: 800, color: '#0f172a' },
  subtitle: { margin: '0 0 22px', fontSize: 14, color: '#6b7280' },
  form: { width: '100%', display: 'flex', flexDirection: 'column', gap: 14 },
  field: { display: 'flex', flexDirection: 'column', gap: 7 },
  label: { fontSize: 13, fontWeight: 500, color: 'rgba(255,255,255,0.7)' },
  input: {
    padding: '12px 14px',
    borderRadius: 12,
    border: '1px solid rgba(15,23,42,0.06)',
    background: '#fff',
    fontSize: 14,
    outline: 'none',
    color: '#0f172a',
    transition: 'box-shadow 0.15s, transform 0.08s',
  },
  errorBox: {
    background: 'rgba(254,205,211,0.8)',
    border: '1px solid rgba(239,68,68,0.12)',
    borderRadius: 10,
    padding: '10px 14px',
    fontSize: 13,
    color: '#991b1b',
  },
  btn: {
    marginTop: 4,
    padding: '12px',
    background: 'linear-gradient(90deg,#7c3aed,#06b6d4)',
    color: '#fff',
    border: 'none',
    borderRadius: 12,
    fontSize: 15,
    fontWeight: 800,
    cursor: 'pointer',
    boxShadow: '0 12px 34px rgba(124,58,237,0.12)',
    transition: 'transform 0.08s, box-shadow 0.12s',
  },
  footer: { marginTop: 20, fontSize: 14, color: '#6b7280' },
  link: { color: '#7c3aed', fontWeight: 700, textDecoration: 'none' },
}
