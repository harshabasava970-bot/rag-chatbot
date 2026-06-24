/**
 * Sidebar panel listing uploaded documents with delete capability.
 */

import { FileText, Trash2, RefreshCw, AlertCircle } from 'lucide-react'
import { useDeleteDocument, useDocuments } from '../hooks/useDocuments'
import DropZone from './DropZone'

function formatBytes(bytes) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDate(isoStr) {
  return new Date(isoStr).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

export default function DocumentPanel() {
  const { data: documents = [], isLoading, isError, refetch } = useDocuments()
  const deleteMutation = useDeleteDocument()

  return (
    <aside className="flex flex-col h-full gap-4">
      {/* Upload section */}
      <div>
        <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-2">
          Upload PDFs
        </h2>
        <DropZone />
      </div>

      {/* Document list */}
      <div className="flex-1 min-h-0 flex flex-col">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
            Documents ({documents.length})
          </h2>
          <button
            onClick={() => refetch()}
            aria-label="Refresh document list"
            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 rounded transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {isError && (
          <div className="flex items-center gap-2 text-red-500 text-xs p-2 bg-red-50 dark:bg-red-900/20 rounded-lg">
            <AlertCircle className="w-4 h-4 shrink-0" />
            Failed to load documents
          </div>
        )}

        <div className="overflow-y-auto flex-1 space-y-2 pr-0.5">
          {documents.length === 0 && !isLoading && (
            <p className="text-xs text-gray-400 dark:text-gray-500 text-center py-6">
              No documents yet. Upload a PDF to get started.
            </p>
          )}

          {documents.map((doc) => (
            <div
              key={doc.id}
              className="group flex items-start gap-2 p-2.5 rounded-lg bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-750 transition-colors"
            >
              <FileText className="w-4 h-4 shrink-0 mt-0.5 text-primary-500" />
              <div className="flex-1 min-w-0">
                <p
                  className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate"
                  title={doc.filename}
                >
                  {doc.filename}
                </p>
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
                  {doc.page_count} pages · {doc.chunk_count} chunks · {formatBytes(doc.file_size)}
                </p>
                <p className="text-xs text-gray-400 dark:text-gray-500">
                  {formatDate(doc.uploaded_at)}
                </p>
              </div>
              <button
                onClick={() => deleteMutation.mutate(doc.id)}
                disabled={deleteMutation.isPending}
                aria-label={`Delete ${doc.filename}`}
                className="p-1 text-gray-300 dark:text-gray-600 hover:text-red-500 dark:hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all rounded shrink-0"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      </div>
    </aside>
  )
}
