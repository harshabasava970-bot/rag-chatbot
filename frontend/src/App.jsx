/**
 * Root application component.
 * Layout: fixed header, two-column main (sidebar + chat), status bar.
 */

import Header from './components/Header'
import DocumentPanel from './components/DocumentPanel'
import ChatWindow from './components/ChatWindow'
import StatusBar from './components/StatusBar'

export default function App() {
  return (
    <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 transition-colors">
      <Header />

      <main className="flex flex-1 min-h-0 overflow-hidden">
        {/* Sidebar – document management */}
        <aside className="hidden md:flex flex-col w-72 xl:w-80 border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4 overflow-y-auto shrink-0">
          <DocumentPanel />
        </aside>

        {/* Chat area */}
        <section className="flex flex-col flex-1 min-w-0 bg-gray-50 dark:bg-gray-950">
          <ChatWindow />
        </section>
      </main>

      <StatusBar />
    </div>
  )
}
