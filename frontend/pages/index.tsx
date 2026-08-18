import React from 'react'

export default function Home() {
  return (
    <div style={{padding:24}}>
      <h1>Agent Fleet Ecom Dashboard (scaffold)</h1>
      <p>Backend API at http://localhost:8000</p>
      <p>Auth endpoints:
        <ul>
          <li>POST /admin/seed-user {"name","email","phone"}</li>
          <li>POST /auth/set-password {"email","password"} (first login sets password)</li>
          <li>POST /auth/login {"email","password"}</li>
        </ul>
      </p>
    </div>
  )
}
