import React from 'react'
import LoginForm from '../components/LoginForm.jsx'

export default function LoginPage() {
  return (
    <div className="min-h-screen grid place-items-center bg-chatbg">
      <div className="w-[90vw] max-w-md rounded-lg border border-white/10 bg-[#202123] p-6">
        <h1 className="mb-4 text-2xl font-semibold">Sign in</h1>
        <LoginForm />
      </div>
    </div>
  )
}









