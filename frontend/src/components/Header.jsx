import { Moon, Sun, FileSearch } from 'lucide-react'
import { useDarkMode } from '../hooks/useDarkMode'

export default function Header() {
  const { isDark, toggle } = useDarkMode()

  return (
    <header className="sticky top-0 z-50 border-b border-gray-200 dark:border-gray-700 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm">
      <div className="max-w-screen-xl mx-auto px-4 h-14 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-primary-600">
            <FileSearch className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-lg text-gray-900 dark:text-white tracking-tight">
            DocChat
          </span>
          <span className="text-xs text-gray-400 dark:text-gray-500 ml-1 hidden sm:inline">
            AI Document Search
          </span>
        </div>

        {/* Dark mode toggle */}
        <button
          onClick={toggle}
          aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
          className="p-2 rounded-lg text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        >
          {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>
      </div>
    </header>
  )
}
