import React, { useEffect, useState } from 'react'

export default function SitesPage(){
  const [reports, setReports] = useState<any>({})
  useEffect(()=>{
    fetch('/agents/reports').then(r=>r.json()).then(setReports).catch(console.error)
  },[])
  return (
    <div style={{padding:20}}>
      <h1>Sites</h1>
      <ul>
        {Object.keys(reports).length===0 && <li>No reports yet</li>}
        {Object.entries(reports).map(([url, rpt]: any)=> (
          <li key={url}>
            <a href={`/site-detail?url=${encodeURIComponent(url)}`}>{url}</a> — score: {rpt.trust_score ?? 'n/a'}
          </li>
        ))}
      </ul>
    </div>
  )
}
