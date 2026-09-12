import { AuthProvider } from './context/AuthContext'
import { SidebarProvider } from './context/SidebarContext'
import { Sidebar } from './components/Sidebar/Sidebar'
import { SignInModal } from './components/Auth/SignInModal'
import { ChatPage } from './pages/ChatPage'
import { useChat } from './hooks/useChat'

function App() {
  const chat = useChat()

  return (
    <AuthProvider>
      <SidebarProvider>
        <div className="flex h-dvh overflow-hidden bg-bg">
          <Sidebar
            onNewChat={chat.startNewChat}
            canStartNewChat={chat.hasStarted && !chat.isSending}
          />
          <ChatPage chat={chat} />
        </div>
        <SignInModal />
      </SidebarProvider>
    </AuthProvider>
  )
}

export default App
