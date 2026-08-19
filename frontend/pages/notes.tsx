import React, {useState, useEffect} from 'react'

export default function Notes(){
  const [to, setTo] = useState('')
  const [subject, setSubject] = useState('')
  const [body, setBody] = useState('')
  const [message, setMessage] = useState('')
  const [notes, setNotes] = useState<any[]>([])

  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null

  const send = async (e:any)=>{
    e.preventDefault()
    setMessage('')
    try{
      const res = await fetch('http://localhost:8000/notes/create', {
        method: 'POST', headers: {'Content-Type':'application/json', 'Authorization': 'Bearer '+token},
        body: JSON.stringify({to_email: to, subject, body})
      })
      if(!res.ok){
        const j = await res.json()
        setMessage(j.detail || 'Failed')
        return
      }
      setMessage('Sent')
      fetchNotes()
    }catch(err){ setMessage('Network error') }
  }

  const fetchNotes = async ()=>{
    try{
      const res = await fetch('http://localhost:8000/notes/list', {headers: {'Authorization': 'Bearer '+token}})
      if(!res.ok) return
      const j = await res.json()
      setNotes(j.notes || [])
    }catch(err){}
  }

  useEffect(()=>{ fetchNotes() }, [])

  return (
    <div style={{padding:24}}>
      <h2>Notes / Notifications</h2>
      <form onSubmit={send}>
        <div><label>To (email)</label><br/><input value={to} onChange={e=>setTo(e.target.value)} /></div>
        <div><label>Subject</label><br/><input value={subject} onChange={e=>setSubject(e.target.value)} /></div>
        <div><label>Body</label><br/><textarea value={body} onChange={e=>setBody(e.target.value)} /></div>
        <div style={{marginTop:12}}><button type="submit">Send Note</button></div>
      </form>
      <div style={{marginTop:12,color:'green'}}>{message}</div>
      <h3 style={{marginTop:24}}>My Notes</h3>
      <ul>
        {notes.map((n,i)=> (
          <li key={i}><strong>{n.subject}</strong> from {n.from}<div>{n.body}</div></li>
        ))}
      </ul>
    </div>
  )
}
