/**
 * Renders a single chat bubble (user or assistant).
 * Assistant messages render Markdown with source citations.
 */

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { User, Bot, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react'
import { useState } from 'react'
import clsx from 'clsx'

function SourceCard({ source, index }) {
  return (
    <div className="text-xs p-2 rounded bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600">
      <div className="flex items-center justify-between gap-2 mb-1">
        <span className="font-semibold text-primary-600 dark:text-primary-400">
          [{index + 1}] {source.filename}
        </span>
        <span className="text-gray-400 dark:text-gray-500 shrink-0">
          {source.page ? `Page ${source.page} · ` : ''}
          {Math.round(source.score * 100)}% match
        </span>
      </div>
      <p className="text-gray-600 dark:text-gray-300 line-clamp-3 leading-relaxed">
        {source.content}
      </p>
    </div>
  )
}

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user'
  const [showSources, setShowSources] = useState(false)
  const hasSources = message.sources && message.sources.length > 0

  return (
    <div
      className={clsx(
        'flex gap-3 animate-slide-up',
        isUser ? 'flex-row-reverse' : 'flex-row',
      )}
    >
      {/* Avatar */}
      <div
        className={clsx(
          'w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-0.5',
          isUser
            ? 'bg-primary-600 text-white'
            : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300',
        )}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Bubble */}
      <div className={clsx('max-w-[80%] space-y-2', isUser ? 'items-end' : 'items-start')}>
        <div
          className={clsx(
            'px-4 py-3 rounded-2xl text-sm leading-relaxed',
            isUser
              ? 'bg-primary-600 text-white rounded-tr-sm'
              : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100 border border-gray-200 dark:border-gray-700 rounded-tl-sm shadow-sm',
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="chat-prose">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Sources toggle */}
        {hasSources && (
          <div className="space-y-1.5">
            <button
              onClick={() => setShowSources((v) => !v)}
              className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
              aria-expanded={showSources}
            >
              {showSources ? (
                <ChevronUp className="w-3.5 h-3.5" />
              ) : (
                <ChevronDown className="w-3.5 h-3.5" />
              )}
              {message.sources.length} source{message.sources.length !== 1 ? 's' : ''}
            </button>

            {showSources && (
              <div className="space-y-1.5 animate-fade-in">
                {message.sources.map((src, i) => (
                  <SourceCard key={i} source={src} index={i} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
