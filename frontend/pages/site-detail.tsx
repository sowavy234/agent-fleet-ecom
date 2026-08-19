import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/router'

export default function SiteDetail(){
  const router = useRouter()
  const { url } = router.query
  const [report, setReport] = useState<any>(null)
  useEffect(()=>{
    if(!url) return
    const u = decodeURIComponent(url as string)
    fetch(`/agents/report?url=${encodeURIComponent(u)}`).then(res=>res.json()).then(setReport).catch(console.error)
  },[url])

  const enqueue = async ()=>{
    const u = decodeURIComponent(url as string)
    const resp = await fetch('/agents/enqueue-check',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:u})})
    const j = await resp.json()
    alert(JSON.stringify(j))
  }

  if(!report) return <div style={{padding:20}}>Loading...</div>
  return (
    <div style={{padding:20}}>
      <h1>Site report for {report.url}</h1>
      <p>Domain: {report.domain}</p>
      <p>Reachable: {String(report.reachable)}</p>
      <p>Status: {report.status_code}</p>
      <p>Score: {report.trust_score}</p>
      <h3>WHOIS</h3>
      <pre>{JSON.stringify(report.whois, null, 2)}</pre>
      <h3>SSL</h3>
      <pre>{JSON.stringify(report.ssl, null, 2)}</pre>
      <h3>Trustpilot</h3>
      <pre>{JSON.stringify(report.trustpilot, null, 2)}</pre>
      <h3>Notes & Contacts</h3>
      <pre>{JSON.stringify({emails: report.contact_emails, phones: report.contact_phones, notes: report.notes}, null, 2)}</pre>
      <button onClick={enqueue}>Enqueue background re-check</button>
    </div>
  )
}
