import React, {useState} from 'react'
import {useRouter} from 'next/router'

export default function Login(){
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')
  const router = useRouter()

  const submit = async (e:any) =>{
    e.preventDefault()
    setMessage('')
    try{
      const res = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({email,password})
      })
      if(!res.ok){
        const j = await res.json()
        // If password not set, prompt user to create one
        if(j.detail && j.detail.toLowerCase().includes('password not set')){
          const ok = confirm('No password set for this account. Set password now?')
          if(ok){
            const pw = prompt('Enter new password')
            if(!pw){
              setMessage('Password not set')
              return
            }
            const setr = await fetch('http://localhost:8000/auth/set-password', {
              method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({email, password: pw})
            })
            if(!setr.ok){
              const sj = await setr.json()
              setMessage('Failed to set password: ' + (sj.detail||setr.statusText))
              return
            }
            // try login again
            const relog = await fetch('http://localhost:8000/auth/login', {
              method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({email, password: pw})
            })
            if(!relog.ok){
              const rj = await relog.json()
              setMessage(rj.detail || 'Login failed after setting password')
              return
            }
            const rj = await relog.json()
            localStorage.setItem('access_token', rj.access_token)
            router.push('/')
            return
          }
        }
        setMessage(j.detail || 'Login failed')
        return
      }
      const j = await res.json()
      localStorage.setItem('access_token', j.access_token)
      setMessage('Login successful')
      router.push('/')
    }catch(err){
      setMessage('Network error')
    }
  }

  return (
    <div style={{padding:24}}>
      <h2>Login (scaffold)</h2>
      <form onSubmit={submit}>
        <div>
          <label>Email</label><br/>
          <input value={email} onChange={e=>setEmail(e.target.value)} />
        </div>
        <div>
          <label>Password</label><br/>
          <input type="password" value={password} onChange={e=>setPassword(e.target.value)} />
        </div>
        <div style={{marginTop:12}}>
          <button type="submit">Login</button>
        </div>
      </form>
      <div style={{marginTop:12,color:'red'}}>{message}</div>
    </div>
  )
}
