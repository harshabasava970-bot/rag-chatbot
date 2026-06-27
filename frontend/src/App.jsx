/**
 * Root application component.
 * Layout: fixed header, two-column main (sidebar + chat), status bar.
 * On mobile: sidebar accessible via a slide-in drawer toggled from the header.
 */

import { useState } from 'react'
import Header from './components/Header'
import DocumentPanel from './components/DocumentPanel'
import ChatWindow from './components/ChatWindow'
import StatusBar from './components/StatusBar'

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 transition-colors">
      <Header onMenuClick={() => setSidebarOpen((v) => !v)} />

      <main className="flex flex-1 min-h-0 overflow-hidden relative">
        {/* Mobile overlay */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-20 bg-black/40 md:hidden"
            onClick={() => setSidebarOpen(false)}
            aria-hidden="true"
          />
        )}

        {/* Sidebar – document management */}
        <aside
          className={[
            'flex flex-col w-72 xl:w-80 border-r border-gray-200 dark:border-gray-700',
            'bg-white dark:bg-gray-900 p-4 overflow-y-auto shrink-0 z-30',
            // Desktop: always visible
            'md:flex md:static',
            // Mobile: slide-in drawer
            sidebarOpen
              ? 'fixed inset-y-0 left-0 flex'
              : 'hidden',
          ].join(' ')}
        >
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
