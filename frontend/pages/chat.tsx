import React, {useEffect, useRef, useState} from 'react'

export default function Chat(){
  const [connected, setConnected] = useState(false)
  const [msgs, setMsgs] = useState<any[]>([])
  const [text, setText] = useState('')
  const [room, setRoom] = useState('default')
  const wsRef = useRef<WebSocket|null>(null)
  const videoRef = useRef<HTMLVideoElement|null>(null)
  const localStreamRef = useRef<MediaStream|null>(null)

  useEffect(()=>{
    return ()=>{
      if(wsRef.current) wsRef.current.close()
      if(localStreamRef.current){
        localStreamRef.current.getTracks().forEach(t=>t.stop())
      }
    }
  },[])

  const connect = ()=>{
    const ws = new WebSocket('ws://localhost:8000/ws/'+room)
    ws.onopen = ()=> setConnected(true)
    ws.onclose = ()=> setConnected(false)
    ws.onmessage = (ev)=>{
      try{
        const j = JSON.parse(ev.data)
        setMsgs(m=>[...m,j])
      }catch(e){
        setMsgs(m=>[...m,{type:'raw', data:ev.data}])
      }
    }
    wsRef.current = ws
  }

  const send = ()=>{
    if(!wsRef.current) return
    const m = {type:'chat', text}
    wsRef.current.send(JSON.stringify(m))
    setMsgs(m=>[...m,{type:'me', text}])
    setText('')
  }

  const startLocalVideo = async ()=>{
    try{
      const s = await navigator.mediaDevices.getUserMedia({video:true,audio:true})
      localStreamRef.current = s
      if(videoRef.current){
        videoRef.current.srcObject = s
        videoRef.current.muted = true
        await videoRef.current.play()
      }
      // send a presence message so other clients may request signaling
      if(wsRef.current) wsRef.current.send(JSON.stringify({type:'presence'}))
    }catch(e){
      console.error('media error', e)
      alert('Failed to access camera/mic: '+String(e))
    }
  }

  return (
    <div style={{padding:24}}>
      <h2>Realtime Chat & Video (basic)</h2>
      <div>
        <label>Room: </label>
        <input value={room} onChange={e=>setRoom(e.target.value)} />
        <button onClick={connect} disabled={connected}>Connect</button>
      </div>
      <div style={{marginTop:12}}>
        <div style={{display:'flex', gap:12}}>
          <div style={{flex:1}}>
            <div style={{height:300,overflow:'auto',border:'1px solid #ddd',padding:8}}>
              {msgs.map((m,i)=>(<div key={i}><b>{m.type}</b>: {m.text||JSON.stringify(m)}</div>))}
            </div>
            <div style={{marginTop:8}}>
              <input value={text} onChange={e=>setText(e.target.value)} style={{width:'70%'}} />
              <button onClick={send}>Send</button>
            </div>
          </div>
          <div style={{width:320}}>
            <video ref={videoRef} style={{width:320,height:240,background:'#000'}} />
            <div style={{marginTop:8}}>
              <button onClick={startLocalVideo}>Start Local Video</button>
              <div style={{fontSize:12,color:'#666'}}>Video is local preview. Full P2P requires signaling handler (server-side) and SimplePeer in browser; this endpoint provides signaling messages via WebSocket 'signal' messages.</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
