import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { getMessages, sendMessage, logout, getMyGroups, getGroupMessages, createGroup, joinGroup, sendGroupMessage, verifyUser, getAllGroups } from '../api'
import useStream from '../components/useStream'

function getPartner(msg, me) {
  return msg.sender === me ? msg.recipient : msg.sender
}

export default function Home() {
  const me = localStorage.getItem('username')
  const navigate = useNavigate()

  // direct messages
  const [allMessages, setAllMessages] = useState([])
  // groups
  const [myGroups, setMyGroups] = useState([])
  const [groupMessages, setGroupMessages] = useState({})
  // persist opened DM conversations across refresh
  const [openedDMs, setOpenedDMs] = useState(() => {
    try { return JSON.parse(localStorage.getItem('openedDMs') || '[]') } catch { return [] }
  })

  // active conversation: { type: 'dm', partner } | { type: 'group', group }
  const [active, setActive] = useState(null)
  const [content, setContent] = useState('')
  const [error, setError] = useState('')

  // modals
  const [modal, setModal] = useState(null) // 'newchat' | 'creategroup' | 'joingroup'
  const [newChatInput, setNewChatInput] = useState({ username: '', email: '' })
  const [createForm, setCreateForm] = useState({ name: '', join_password: '' })
  const [joinForm, setJoinForm] = useState({ search: '', password: '', selectedId: null })
  const [allGroupsList, setAllGroupsList] = useState([])
  const [filteredGroups, setFilteredGroups] = useState([])
  const [modalError, setModalError] = useState('')

  const bottomRef = useRef()

  useEffect(() => {
    getMessages().then(setAllMessages).catch(() => {})
    getMyGroups().then(setMyGroups).catch(() => {})
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [active, allMessages, groupMessages])

  useStream((msg) => {
    if (msg.type === 'group') {
      setGroupMessages((prev) => {
        const existing = prev[msg.group_id] || []
        if (existing.find((m) => m.id === msg.id)) return prev
        return { ...prev, [msg.group_id]: [...existing, msg] }
      })
    } else {
      setAllMessages((prev) => prev.find((m) => m.id === msg.id) ? prev : [...prev, msg])
    }
  })

  const selectDM = (partner) => {
    setActive({ type: 'dm', partner })
    setError('')
    setOpenedDMs((prev) => {
      const updated = prev.includes(partner) ? prev : [...prev, partner]
      localStorage.setItem('openedDMs', JSON.stringify(updated))
      return updated
    })
  }

  const selectGroup = async (group) => {
    setActive({ type: 'group', group })
    setError('')
    try {
      const history = await getGroupMessages(group.id)
      setGroupMessages((prev) => ({ ...prev, [group.id]: history }))
    } catch {}
  }

  const handleSend = async (e) => {
    e.preventDefault()
    if (!content.trim()) return
    setError('')
    try {
      if (active.type === 'dm') {
        await sendMessage(active.partner, content)
      } else {
        await sendGroupMessage(active.group.id, content)
      }
      setContent('')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send')
    }
  }

  const handleNewChat = async (e) => {
    e.preventDefault()
    setModalError('')
    try {
      await verifyUser(newChatInput.username.trim(), newChatInput.email.trim())
      selectDM(newChatInput.username.trim())
      setNewChatInput({ username: '', email: '' })
      setModal(null)
    } catch {
      setModalError('User not found or email does not match')
    }
  }

  const handleCreateGroup = async (e) => {
    e.preventDefault()
    setModalError('')
    try {
      const g = await createGroup(createForm.name, createForm.join_password || undefined)
      setMyGroups((prev) => [...prev, g])
      setCreateForm({ name: '', join_password: '' })
      setModal(null)
      await selectGroup(g)
    } catch (err) {
      setModalError(err.response?.data?.detail || 'Failed')
    }
  }

  const openJoinModal = async () => {
    setModal('joingroup')
    setModalError('')
    try {
      const groups = await getAllGroups()
      setAllGroupsList(groups)
      setFilteredGroups(groups)
    } catch {}
  }

  const handleJoinSearch = (val) => {
    setJoinForm((prev) => ({ ...prev, search: val }))
    setFilteredGroups(allGroupsList.filter((g) => g.name.toLowerCase().includes(val.toLowerCase())))
  }

  const handleJoinGroup = async (e) => {
    e.preventDefault()
    setModalError('')
    try {
      const groups = await getAllGroups()
      const found = groups.find((g) => g.name.toLowerCase() === joinForm.search.trim().toLowerCase())
      if (!found) { setModalError('Group not found'); return }
      const r = await joinGroup(found.id, joinForm.password || null)
      if (r.status === 'approved') {
        const updated = await getMyGroups()
        setMyGroups(updated)
        const joined = updated.find((g) => g.id === found.id)
        setJoinForm({ search: '', password: '', selectedId: null })
        setModal(null)
        if (joined) await selectGroup(joined)
      } else {
        setModalError('Join request pending approval')
      }
    } catch (err) {
      setModalError(err.response?.data?.detail || 'Failed')
    }
  }

  const dmConversations = [...new Set([...openedDMs, ...allMessages.map((m) => getPartner(m, me))])]

  const activeMessages = !active ? [] :
    active.type === 'dm'
      ? allMessages.filter((m) => getPartner(m, me) === active.partner)
      : (groupMessages[active.group.id] || [])

  const activeName = !active ? '' :
    active.type === 'dm' ? active.partner : `# ${active.group.name}`

  return (
    <div style={s.page}>
      <div style={s.container}>
      {/* Sidebar */}
  <div style={s.sidebar}>
        <div style={s.sidebarTop}>
          <span style={s.appName}>💬 Messenger</span>
          <button style={s.logoutBtn} onClick={() => { localStorage.removeItem('openedDMs'); logout(); navigate('/login') }}>Logout</button>
        </div>
        <div style={s.meLabel}>@{me}</div>

        {/* Direct Messages */}
        <div style={s.section}>
          <div style={s.sectionHeader}>
            <span>Direct Messages</span>
            <button style={s.addBtn} onClick={() => { setModal('newchat'); setModalError('') }}>+</button>
          </div>
          {dmConversations.map((partner) => (
            <button
              key={partner}
              style={{ ...s.item, ...(active?.type === 'dm' && active.partner === partner ? s.itemActive : {}) }}
              onClick={() => selectDM(partner)}
            >
              <span style={s.avatar}>{partner[0]?.toUpperCase()}</span>
              <span style={s.itemName}>{partner}</span>
            </button>
          ))}
        </div>

        {/* Groups */}
        <div style={s.section}>
          <div style={s.sectionHeader}>
            <span>Groups</span>
            <div style={{ display: 'flex', gap: 4 }}>
              <button style={s.addBtn} onClick={() => { setModal('creategroup'); setModalError('') }} title="Create">+</button>
              <button style={s.addBtn} onClick={openJoinModal} title="Join">↩</button>
            </div>
          </div>
          {myGroups.map((g) => (
            <button
              key={g.id}
              style={{ ...s.item, ...(active?.type === 'group' && active.group.id === g.id ? s.itemActive : {}) }}
              onClick={() => selectGroup(g)}
            >
              <span style={{ ...s.avatar, background: '#a6e3a1' }}>#</span>
              <span style={s.itemName}>{g.name}</span>
              {g.owner === me && <span style={s.ownerBadge}>owner</span>}
            </button>
          ))}
        </div>
      </div>

      {/* Main */}
  <div style={s.mainPanel}>
        {!active ? (
          <div style={s.empty}>Select a conversation or start a new one</div>
        ) : (
          <>
            <div style={s.chatHeader}>
              <span style={s.chatTitle}>{activeName}</span>
              {active.type === 'group' && (
                <span style={s.chatSub}>id: {active.group.id} · owner: {active.group.owner}</span>
              )}
            </div>
            <div style={s.messages}>
              {activeMessages.length === 0 && <p style={s.noMsg}>No messages yet 👋</p>}
              {activeMessages.map((m, i) => {
                const isMe = m.sender === me
                return (
                  <div key={m.id ?? i} style={{ ...s.msgRow, justifyContent: isMe ? 'flex-end' : 'flex-start' }}>
                    <div style={s.msgWrap}>
                      {!isMe && <span style={s.sender}>{m.sender}</span>}
                      <div style={{ ...s.bubble, ...(isMe ? s.bubbleMe : s.bubbleThem) }}>
                        {m.content}
                      </div>
                    </div>
                  </div>
                )
              })}
              <div ref={bottomRef} />
            </div>
            <form onSubmit={handleSend} style={s.inputRow}>
              <input
                style={{ ...s.input, flex: 1 }}
                placeholder={`Message ${activeName}...`}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                required
              />
              <button style={s.sendBtn} type="submit">Send</button>
            </form>
            {error && <p style={s.error}>{error}</p>}
          </>
        )}
      </div>

      {/* Modals */}
      {modal && (
        <div style={s.overlay} onClick={() => setModal(null)}>
          <div style={s.modal} onClick={(e) => e.stopPropagation()}>
            {modal === 'newchat' && (
              <>
                <h3 style={s.modalTitle}>New Direct Message</h3>
                <form onSubmit={handleNewChat} style={s.modalForm}>
                  <input style={s.modalInput} placeholder="Username" value={newChatInput.username} onChange={(e) => setNewChatInput({ ...newChatInput, username: e.target.value })} autoFocus required />
                  <input style={s.modalInput} placeholder="Email" type="email" value={newChatInput.email} onChange={(e) => setNewChatInput({ ...newChatInput, email: e.target.value })} required />
                  {modalError && <p style={s.error}>{modalError}</p>}
                  <button style={s.modalBtn} type="submit">Start Chat</button>
                </form>
              </>
            )}
            {modal === 'creategroup' && (
              <>
                <h3 style={s.modalTitle}>Create Group</h3>
                <form onSubmit={handleCreateGroup} style={s.modalForm}>
                  <input style={s.modalInput} placeholder="Group name" value={createForm.name} onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })} autoFocus required />
                  <input style={s.modalInput} placeholder="Join password (optional)" value={createForm.join_password} onChange={(e) => setCreateForm({ ...createForm, join_password: e.target.value })} />
                  {modalError && <p style={s.error}>{modalError}</p>}
                  <button style={s.modalBtn} type="submit">Create</button>
                </form>
              </>
            )}
            {modal === 'joingroup' && (
              <>
                <h3 style={s.modalTitle}>Join Group</h3>
                <form onSubmit={handleJoinGroup} style={s.modalForm}>
                  <input
                    style={s.modalInput}
                    placeholder="Group name"
                    value={joinForm.search}
                    onChange={(e) => setJoinForm((prev) => ({ ...prev, search: e.target.value, selectedId: null }))}
                    autoFocus
                    required
                  />
                  <input style={s.modalInput} placeholder="Password (if required)" value={joinForm.password} onChange={(e) => setJoinForm((prev) => ({ ...prev, password: e.target.value }))} />
                  {modalError && <p style={s.error}>{modalError}</p>}
                  <button style={s.modalBtn} type="submit">Join</button>
                </form>
              </>
            )}
          </div>
        </div>
      )}
      </div>
    </div>
  )
}

const s = {
  page: {
    display: 'flex',
    height: '100vh',
    fontFamily: "Inter, 'Segoe UI', Roboto, sans-serif",
    background: 'linear-gradient(180deg, #f7fbff 0%, #f3f7fb 100%)',
  },
  sidebar: {
    width: 300,
    background: 'linear-gradient(180deg, #4f46e5 0%, #7c3aed 100%)',
    display: 'flex',
    flexDirection: 'column',
    color: '#f8fafc',
    overflowY: 'auto',
    boxShadow: 'none',
    borderTopLeftRadius: 14,
    borderBottomLeftRadius: 14,
  },
  sidebarTop: {
    padding: '18px 16px',
    borderBottom: '1px solid rgba(255,255,255,0.06)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    position: 'sticky',
    top: 0,
    background: 'transparent',
    zIndex: 1,
  },
  appName: { fontWeight: 800, fontSize: 16, letterSpacing: 0.2 },
  logoutBtn: {
    background: 'rgba(255,255,255,0.12)',
    border: '1px solid rgba(255,255,255,0.16)',
    color: '#fff',
    borderRadius: 10,
    padding: '6px 10px',
    cursor: 'pointer',
    fontSize: 12,
  },
  meLabel: { padding: '8px 16px', fontSize: 13, color: 'rgba(255,255,255,0.9)' },
  section: { padding: '10px 0' },
  sectionHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '6px 16px',
    fontSize: 12,
    fontWeight: 700,
    color: 'rgba(255,255,255,0.85)',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  addBtn: { background: 'rgba(255,255,255,0.06)', border: 'none', color: '#fff', cursor: 'pointer', fontSize: 16, lineHeight: 1, padding: '6px 8px', borderRadius: 8 },
  item: {
    width: '100%',
    background: 'transparent',
    border: 'none',
    color: '#fff',
    padding: '10px 16px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    textAlign: 'left',
    transition: 'background 180ms ease',
  },
  itemActive: { background: 'rgba(255,255,255,0.06)' },
  avatar: {
    width: 36,
    height: 36,
    borderRadius: '50%',
    background: 'linear-gradient(135deg,#ff7ab6 0%,#7c3aed 100%)',
    color: '#fff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 700,
    fontSize: 14,
    flexShrink: 0,
  },
  itemName: { fontSize: 15, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 },
  ownerBadge: { fontSize: 11, background: 'rgba(255,255,255,0.12)', color: '#fff', borderRadius: 6, padding: '2px 6px', flexShrink: 0 },
  main: { flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' },

  /* container wraps sidebar + main to create a centered card */
  container: {
    width: 'min(1100px, 96%)',
    height: '92vh',
    margin: '4vh auto',
    display: 'flex',
    borderRadius: 14,
    overflow: 'hidden',
    background: 'linear-gradient(180deg, rgba(255,255,255,0.8), rgba(248,250,252,0.7))',
    boxShadow: '0 20px 60px rgba(2,6,23,0.12)',
    border: '1px solid rgba(15,23,42,0.06)',
  },

  /* give the main panel a soft right-side radius and subtle background */
  mainPanel: { flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', borderTopRightRadius: 14, borderBottomRightRadius: 14, background: 'linear-gradient(180deg,#ffffff,#fbfdff)' },
  empty: { flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#6b7280', fontSize: 16 },
  chatHeader: { padding: '16px 22px', borderBottom: '1px solid rgba(0,0,0,0.06)', background: 'linear-gradient(90deg,#ffffff, #fbfdff)', display: 'flex', alignItems: 'baseline', gap: 12 },
  chatTitle: { fontWeight: 800, fontSize: 18, color: '#0f172a' },
  chatSub: { fontSize: 12, color: '#6b7280' },
  messages: { flex: 1, overflowY: 'auto', padding: '18px 24px', display: 'flex', flexDirection: 'column', gap: 8, background: 'transparent' },
  noMsg: { color: '#9ca3af', textAlign: 'center', marginTop: 40 },
  msgRow: { display: 'flex' },
  msgWrap: { display: 'flex', flexDirection: 'column', maxWidth: '72%', gap: 6 },
  sender: { fontSize: 12, color: '#6b7280', marginBottom: 6, paddingLeft: 6 },
  bubble: { padding: '10px 16px', borderRadius: 18, fontSize: 15, lineHeight: 1.4, wordBreak: 'break-word' },
  bubbleMe: {
    background: 'linear-gradient(135deg,#7c3aed 0%,#06b6d4 100%)',
    color: '#fff',
    borderBottomRightRadius: 8,
    borderTopRightRadius: 18,
    borderTopLeftRadius: 18,
    boxShadow: '0 10px 30px rgba(124,58,237,0.12)'
  },
  bubbleThem: {
    background: '#ffffff',
    color: '#0f172a',
    border: '1px solid rgba(15,23,42,0.04)',
    borderBottomLeftRadius: 8,
    borderTopLeftRadius: 18,
    borderTopRightRadius: 18,
    boxShadow: '0 6px 20px rgba(2,6,23,0.04)'
  },
  inputRow: { display: 'flex', gap: 12, padding: '14px 18px', borderTop: '1px solid rgba(15,23,42,0.04)', background: 'linear-gradient(90deg,#ffffff, #fbfdff)', alignItems: 'center' },
  input: { padding: '12px 16px', borderRadius: 14, border: '1px solid rgba(15,23,42,0.06)', fontSize: 15, outline: 'none', boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.6)' },
  sendBtn: { background: 'linear-gradient(90deg,#ff7ab6,#7c3aed)', color: '#fff', border: 'none', borderRadius: 14, padding: '10px 22px', cursor: 'pointer', fontWeight: 800, boxShadow: '0 12px 34px rgba(124,58,237,0.12)' },
  error: { color: '#ef4444', margin: '0 18px 10px', fontSize: 13 },
  overlay: { position: 'fixed', inset: 0, background: 'rgba(2,6,23,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 },
  modal: { background: '#ffffff', borderRadius: 14, padding: 28, width: 360, display: 'flex', flexDirection: 'column', gap: 12, boxShadow: '0 12px 40px rgba(2,6,23,0.16)' },
  modalTitle: { margin: 0, fontSize: 18, color: '#0f172a' },
  modalForm: { display: 'flex', flexDirection: 'column', gap: 10 },
  modalInput: { padding: '10px 12px', borderRadius: 10, border: '1px solid rgba(15,23,42,0.06)', fontSize: 14, outline: 'none' },
  modalBtn: { background: 'linear-gradient(90deg,#7c3aed,#06b6d4)', color: '#fff', border: 'none', borderRadius: 10, padding: 10, cursor: 'pointer', fontWeight: 700, fontSize: 15 },
  groupSearchList: { maxHeight: 220, overflowY: 'auto', border: '1px solid rgba(15,23,42,0.04)', borderRadius: 10, display: 'flex', flexDirection: 'column' },
  groupSearchItem: { background: 'transparent', border: 'none', padding: '10px 14px', cursor: 'pointer', display: 'flex', flexDirection: 'column', textAlign: 'left', borderBottom: '1px solid rgba(15,23,42,0.03)' },
  groupSearchItemActive: { background: 'rgba(59,130,246,0.06)' },
}

