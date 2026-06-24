/** Animated three-dot typing indicator shown while the AI is thinking. */

import { Bot } from 'lucide-react'

export default function TypingIndicator() {
  return (
    <div className="flex gap-3 animate-fade-in">
      <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
        <Bot className="w-4 h-4" />
      </div>
      <div className="px-4 py-3 rounded-2xl rounded-tl-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm">
        <div className="flex items-center gap-1 h-4">
          <div className="w-2 h-2 rounded-full bg-gray-400 dark:bg-gray-500 typing-dot" />
          <div className="w-2 h-2 rounded-full bg-gray-400 dark:bg-gray-500 typing-dot" />
          <div className="w-2 h-2 rounded-full bg-gray-400 dark:bg-gray-500 typing-dot" />
        </div>
      </div>
    </div>
  )
}
