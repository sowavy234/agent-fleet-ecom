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
