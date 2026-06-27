/**
 * Bottom status bar showing API health information.
 */

import { useQuery } from '@tanstack/react-query'
import { CheckCircle, XCircle, Loader } from 'lucide-react'
import { getHealth } from '../services/api'

export default function StatusBar() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
    refetchInterval: 60_000, // check every minute
    retry: 1,
  })

  return (
    <div className="flex items-center gap-4 px-4 py-1.5 text-xs text-gray-400 dark:text-gray-500 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
      {isLoading && (
        <span className="flex items-center gap-1">
          <Loader className="w-3 h-3 animate-spin" /> Checking status…
        </span>
      )}
      {isError && (
        <span className="flex items-center gap-1 text-red-400">
          <XCircle className="w-3 h-3" /> Backend unreachable
        </span>
      )}
      {data && (
        <>
          <span className="flex items-center gap-1">
            {data.openai_connected ? (
              <CheckCircle className="w-3 h-3 text-green-500" />
            ) : (
              <XCircle className="w-3 h-3 text-red-400" />
            )}
            Groq
          </span>
          <span className="flex items-center gap-1">
            <CheckCircle className="w-3 h-3 text-green-500" />
            {data.vector_store === 'pinecone' ? 'Pinecone' : 'FAISS (local)'}
          </span>
          <span>{data.document_count} doc{data.document_count !== 1 ? 's' : ''} indexed</span>
          <span className="ml-auto">v{data.version}</span>
        </>
      )}
    </div>
  )
}
