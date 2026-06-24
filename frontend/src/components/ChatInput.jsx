/**
 * Chat input bar with auto-resize textarea and send button.
 * Supports Shift+Enter for newlines, Enter to submit.
 */

import { useRef, useState, useEffect } from 'react'
import { Send, Square } from 'lucide-react'
import clsx from 'clsx'

export default function ChatInput({ onSend, isLoading, disabled }) {
  const [value, setValue] = useState('')
  const textareaRef = useRef(null)

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current
    if (!ta) return
    ta.style.height = 'auto'
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`
  }, [value])

  const handleSubmit = () => {
    const trimmed = value.trim()
    if (!trimmed || isLoading || disabled) return
    onSend(trimmed)
    setValue('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="flex items-end gap-2 p-3 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
      <div className="flex-1 flex items-end gap-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800 px-3 py-2 focus-within:border-primary-500 dark:focus-within:border-primary-500 transition-colors">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          placeholder={disabled ? 'Upload a PDF to start chatting…' : 'Ask a question about your documents…'}
          disabled={isLoading || disabled}
          aria-label="Chat input"
          className="flex-1 bg-transparent text-sm text-gray-800 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 resize-none outline-none leading-relaxed disabled:opacity-50"
        />
      </div>
      <button
        onClick={handleSubmit}
        disabled={!value.trim() || isLoading || disabled}
        aria-label="Send message"
        className={clsx(
          'w-9 h-9 flex items-center justify-center rounded-lg transition-colors shrink-0',
          !value.trim() || isLoading || disabled
            ? 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
            : 'bg-primary-600 hover:bg-primary-700 text-white',
        )}
      >
        <Send className="w-4 h-4" />
      </button>
    </div>
  )
}
