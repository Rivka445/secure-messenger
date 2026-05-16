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
    background: 'linear-gradient(135deg, #1e1e2e 0%, #313244 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontFamily: "'Segoe UI', sans-serif",
    padding: 16,
  },
  card: {
    background: '#fff',
    borderRadius: 20,
    padding: '40px 36px',
    width: '100%',
    maxWidth: 400,
    boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  logo: { fontSize: 48, marginBottom: 8 },
  title: { margin: '0 0 4px', fontSize: 24, fontWeight: 700, color: '#1e1e2e' },
  subtitle: { margin: '0 0 28px', fontSize: 14, color: '#888' },
  form: { width: '100%', display: 'flex', flexDirection: 'column', gap: 16 },
  field: { display: 'flex', flexDirection: 'column', gap: 6 },
  label: { fontSize: 13, fontWeight: 600, color: '#444' },
  hint: { fontWeight: 400, color: '#aaa', fontSize: 12 },
  input: {
    padding: '11px 14px',
    borderRadius: 10,
    border: '1.5px solid #e0e0e0',
    fontSize: 14,
    outline: 'none',
    color: '#1e1e2e',
  },
  errorBox: {
    background: '#fff0f0',
    border: '1px solid #ffcccc',
    borderRadius: 8,
    padding: '10px 14px',
    fontSize: 13,
    color: '#cc0000',
    display: 'flex',
    gap: 6,
    alignItems: 'center',
  },
  btn: {
    marginTop: 4,
    padding: '12px',
    background: 'linear-gradient(135deg, #0084ff, #0060cc)',
    color: '#fff',
    border: 'none',
    borderRadius: 10,
    fontSize: 15,
    fontWeight: 700,
    cursor: 'pointer',
    boxShadow: '0 4px 14px rgba(0,132,255,0.4)',
  },
  footer: { marginTop: 24, fontSize: 14, color: '#666' },
  link: { color: '#0084ff', fontWeight: 600, textDecoration: 'none' },
}
