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
      const r = await joinGroup(found.id, joinForm.password || undefined)
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
      <div style={s.main}>
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
  )
}

const s = {
  page: { display: 'flex', height: '100vh', fontFamily: 'sans-serif', background: '#f0f2f5' },
  sidebar: { width: 260, background: '#1e1e2e', display: 'flex', flexDirection: 'column', color: '#cdd6f4', overflowY: 'auto' },
  sidebarTop: { padding: '14px 12px 6px', borderBottom: '1px solid #313244', display: 'flex', alignItems: 'center', justifyContent: 'space-between', position: 'sticky', top: 0, background: '#1e1e2e', zIndex: 1 },
  appName: { fontWeight: 700, fontSize: 15 },
  logoutBtn: { background: 'none', border: '1px solid #45475a', color: '#cdd6f4', borderRadius: 6, padding: '3px 8px', cursor: 'pointer', fontSize: 11 },
  meLabel: { padding: '4px 14px 8px', fontSize: 12, color: '#6c7086' },
  section: { padding: '8px 0' },
  sectionHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 14px 4px', fontSize: 11, fontWeight: 700, color: '#6c7086', textTransform: 'uppercase', letterSpacing: 1 },
  addBtn: { background: 'none', border: 'none', color: '#6c7086', cursor: 'pointer', fontSize: 16, lineHeight: 1, padding: '0 2px' },
  item: { width: '100%', background: 'none', border: 'none', color: '#cdd6f4', padding: '7px 14px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 10, textAlign: 'left' },
  itemActive: { background: '#313244' },
  avatar: { width: 30, height: 30, borderRadius: '50%', background: '#89b4fa', color: '#1e1e2e', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 13, flexShrink: 0 },
  itemName: { fontSize: 14, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 },
  ownerBadge: { fontSize: 10, background: '#a6e3a1', color: '#1e1e2e', borderRadius: 4, padding: '1px 4px', flexShrink: 0 },
  main: { flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' },
  empty: { flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#888', fontSize: 16 },
  chatHeader: { padding: '12px 20px', borderBottom: '1px solid #ddd', background: '#fff', display: 'flex', alignItems: 'baseline', gap: 12 },
  chatTitle: { fontWeight: 700, fontSize: 17 },
  chatSub: { fontSize: 12, color: '#888' },
  messages: { flex: 1, overflowY: 'auto', padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: 6 },
  noMsg: { color: '#aaa', textAlign: 'center', marginTop: 40 },
  msgRow: { display: 'flex' },
  msgWrap: { display: 'flex', flexDirection: 'column', maxWidth: '65%' },
  sender: { fontSize: 11, color: '#666', marginBottom: 2, paddingLeft: 4 },
  bubble: { padding: '8px 14px', borderRadius: 18, fontSize: 14, lineHeight: 1.4 },
  bubbleMe: { background: '#0084ff', color: '#fff', borderBottomRightRadius: 4 },
  bubbleThem: { background: '#fff', color: '#111', borderBottomLeftRadius: 4, boxShadow: '0 1px 2px rgba(0,0,0,0.1)' },
  inputRow: { display: 'flex', gap: 8, padding: '12px 16px', borderTop: '1px solid #ddd', background: '#fff' },
  input: { padding: '8px 12px', borderRadius: 8, border: '1px solid #ddd', fontSize: 14, outline: 'none' },
  sendBtn: { background: '#0084ff', color: '#fff', border: 'none', borderRadius: 8, padding: '8px 20px', cursor: 'pointer', fontWeight: 600 },
  error: { color: 'red', margin: '0 16px 8px', fontSize: 13 },
  overlay: { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 },
  modal: { background: '#fff', borderRadius: 12, padding: 28, width: 320, display: 'flex', flexDirection: 'column', gap: 12 },
  modalTitle: { margin: 0, fontSize: 18 },
  modalForm: { display: 'flex', flexDirection: 'column', gap: 10 },
  modalInput: { padding: '9px 12px', borderRadius: 8, border: '1px solid #ddd', fontSize: 14, outline: 'none' },
  modalBtn: { background: '#0084ff', color: '#fff', border: 'none', borderRadius: 8, padding: 10, cursor: 'pointer', fontWeight: 600, fontSize: 15 },
  groupSearchList: { maxHeight: 180, overflowY: 'auto', border: '1px solid #eee', borderRadius: 8, display: 'flex', flexDirection: 'column' },
  groupSearchItem: { background: 'none', border: 'none', padding: '8px 12px', cursor: 'pointer', display: 'flex', flexDirection: 'column', textAlign: 'left', borderBottom: '1px solid #f0f0f0' },
  groupSearchItemActive: { background: '#e8f0fe' },
}
