import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { registerUser } from '../api'

export default function Register() {
  const [form, setForm] = useState({ username: '', password: '', email: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handle = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await registerUser(form.username, form.password, form.email || undefined)
      navigate('/login')
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={s.page}>
      <div style={s.card}>
        <div style={s.logo}>💬</div>
        <h1 style={s.title}>Create Account</h1>
        <p style={s.subtitle}>Join Secure Messenger today</p>

        <form onSubmit={submit} style={s.form}>
          <div style={s.field}>
            <label style={s.label}>Username <span style={s.hint}>(min 3 characters)</span></label>
            <input
              style={s.input}
              name="username"
              placeholder="Choose a username"
              value={form.username}
              onChange={handle}
              required
              autoFocus
            />
          </div>
          <div style={s.field}>
            <label style={s.label}>Password <span style={s.hint}>(min 6 characters)</span></label>
            <input
              style={s.input}
              name="password"
              type="password"
              placeholder="Choose a password"
              value={form.password}
              onChange={handle}
              required
            />
          </div>
          <div style={s.field}>
            <label style={s.label}>Email</label>
            <input
              style={s.input}
              name="email"
              type="email"
              placeholder="your@email.com"
              value={form.email}
              onChange={handle}
              required
            />
          </div>

          {error && (
            <div style={s.errorBox}>
              <span>⚠️</span> {error}
            </div>
          )}

          <button style={{ ...s.btn, opacity: loading ? 0.7 : 1 }} type="submit" disabled={loading}>
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <p style={s.footer}>
          Already have an account?{' '}
          <Link to="/login" style={s.link}>Sign in</Link>
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
  },
  glow: {
    position: 'absolute',
    width: 360,
    height: 360,
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(124,58,237,0.12) 0%, rgba(6,182,212,0.06) 50%, transparent 70%)',
    top: '18%',
    right: '14%',
    transform: 'translate(10%, -10%)',
    pointerEvents: 'none',
  },
  card: {
    background: 'linear-gradient(180deg, rgba(255,255,255,0.95), rgba(251,253,255,0.98))',
    borderRadius: 20,
    padding: '36px 34px',
    width: '100%',
    maxWidth: 480,
    boxShadow: '0 18px 50px rgba(2,6,23,0.08)',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    position: 'relative'
  },
  logo: { fontSize: 44, marginBottom: 8, background: 'linear-gradient(135deg,#ff7ab6,#7c3aed)', WebkitBackgroundClip: 'text', color: 'transparent' },
  title: { margin: '0 0 4px', fontSize: 24, fontWeight: 800, color: '#0f172a' },
  subtitle: { margin: '0 0 22px', fontSize: 14, color: '#6b7280' },
  form: { width: '100%', display: 'flex', flexDirection: 'column', gap: 16 },
  field: { display: 'flex', flexDirection: 'column', gap: 6 },
  label: { fontSize: 13, fontWeight: 600, color: '#444' },
  hint: { fontWeight: 400, color: '#aaa', fontSize: 12 },
  input: {
    padding: '12px 14px',
    borderRadius: 12,
    border: '1px solid rgba(15,23,42,0.06)',
    fontSize: 14,
    outline: 'none',
    color: '#0f172a',
    background: '#fff'
  },
  errorBox: {
    background: 'rgba(254,205,211,0.9)',
    border: '1px solid rgba(239,68,68,0.12)',
    borderRadius: 10,
    padding: '10px 14px',
    fontSize: 13,
    color: '#991b1b',
    display: 'flex',
    gap: 6,
    alignItems: 'center',
  },
  btn: {
    marginTop: 4,
    padding: '12px',
    background: 'linear-gradient(90deg,#ff7ab6,#7c3aed)',
    color: '#fff',
    border: 'none',
    borderRadius: 12,
    fontSize: 15,
    fontWeight: 800,
    cursor: 'pointer',
    boxShadow: '0 12px 34px rgba(124,58,237,0.12)'
  },
  footer: { marginTop: 24, fontSize: 14, color: '#6b7280' },
  link: { color: '#7c3aed', fontWeight: 700, textDecoration: 'none' },
}
