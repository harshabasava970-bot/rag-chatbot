/**
 * Main chat window component.
 * Combines the message list, typing indicator, and input bar.
 */

import { useEffect, useRef } from 'react'
import { MessageSquare, Trash2 } from 'lucide-react'
import { useChat } from '../hooks/useChat'
import { useDocuments } from '../hooks/useDocuments'
import ChatMessage from './ChatMessage'
import ChatInput from './ChatInput'
import TypingIndicator from './TypingIndicator'

export default function ChatWindow() {
  const { messages, isLoading, sendMessage, clearConversation } = useChat()
  const { data: documents = [] } = useDocuments()
  const bottomRef = useRef(null)

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const hasDocuments = documents.length > 0

  return (
    <div className="flex flex-col h-full">
      {/* Chat header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-primary-500" />
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Chat
          </span>
          {messages.length > 0 && (
            <span className="text-xs text-gray-400 dark:text-gray-500">
              · {messages.length} message{messages.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>
        {messages.length > 0 && (
          <button
            onClick={clearConversation}
            aria-label="Clear conversation"
            className="flex items-center gap-1 text-xs text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Clear
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center gap-3 text-gray-400 dark:text-gray-500">
            <MessageSquare className="w-12 h-12 opacity-30" />
            <div>
              <p className="font-medium text-gray-500 dark:text-gray-400">
                {hasDocuments
                  ? 'Ask anything about your documents'
                  : 'Upload a PDF to get started'}
              </p>
              <p className="text-xs mt-1 text-gray-400 dark:text-gray-500">
                {hasDocuments
                  ? `${documents.length} document${documents.length > 1 ? 's' : ''} ready`
                  : 'Drag and drop PDFs in the sidebar'}
              </p>
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}

        {isLoading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <ChatInput
        onSend={sendMessage}
        isLoading={isLoading}
        disabled={!hasDocuments}
      />
    </div>
  )
}
