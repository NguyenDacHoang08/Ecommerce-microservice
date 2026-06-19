import { Outlet } from 'react-router-dom'
import Header from './Header'
import Footer from './Footer'
import ChatBot from '@/components/ChatBot'

const MainLayout = () => {
  return (
    <div className="flex min-h-screen flex-col bg-background font-sans antialiased">
      <Header />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
      <ChatBot />
    </div>
  )
}

export default MainLayout
