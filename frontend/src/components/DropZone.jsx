/**
 * Drag-and-drop PDF upload zone.
 * Uses react-dropzone and shows per-file upload progress.
 */

import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, File, X, CheckCircle, AlertCircle } from 'lucide-react'
import clsx from 'clsx'
import { useUploadDocument } from '../hooks/useDocuments'

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function DropZone() {
  const uploadMutation = useUploadDocument()
  const [fileStates, setFileStates] = useState([]) // {name, status, progress, error}

  const processFile = useCallback(async (file) => {
    const entry = { name: file.name, status: 'uploading', progress: 0, error: null }
    setFileStates((prev) => [...prev, entry])

    const onProgress = (pct) =>
      setFileStates((prev) =>
        prev.map((f) => (f.name === file.name ? { ...f, progress: pct } : f))
      )

    try {
      await uploadMutation.mutateAsync({ file, onProgress })
      setFileStates((prev) =>
        prev.map((f) => (f.name === file.name ? { ...f, status: 'done' } : f))
      )
      // Auto-remove success entry after 3 s
      setTimeout(() => {
        setFileStates((prev) => prev.filter((f) => f.name !== file.name))
      }, 3000)
    } catch (err) {
      setFileStates((prev) =>
        prev.map((f) =>
          f.name === file.name ? { ...f, status: 'error', error: err.message } : f
        )
      )
    }
  }, [uploadMutation])

  const onDrop = useCallback(
    (acceptedFiles) => {
      acceptedFiles.forEach((f) => processFile(f))
    },
    [processFile],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    multiple: true,
    maxSize: 50 * 1024 * 1024, // 50 MB
  })

  const removeEntry = (name) =>
    setFileStates((prev) => prev.filter((f) => f.name !== name))

  return (
    <div className="space-y-3">
      {/* Drop area */}
      <div
        {...getRootProps()}
        className={clsx(
          'border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors select-none',
          isDragActive
            ? 'border-primary-500 bg-primary-50 dark:bg-primary-950'
            : 'border-gray-300 dark:border-gray-600 hover:border-primary-400 hover:bg-gray-50 dark:hover:bg-gray-800',
        )}
        role="button"
        aria-label="Upload PDF files"
      >
        <input {...getInputProps()} />
        <Upload className="w-8 h-8 mx-auto mb-2 text-gray-400 dark:text-gray-500" />
        {isDragActive ? (
          <p className="text-primary-600 dark:text-primary-400 font-medium text-sm">
            Drop PDFs here…
          </p>
        ) : (
          <>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              <span className="font-medium text-primary-600 dark:text-primary-400">
                Click to upload
              </span>{' '}
              or drag &amp; drop
            </p>
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">PDF up to 50 MB</p>
          </>
        )}
      </div>

      {/* Per-file progress */}
      {fileStates.map((f) => (
        <div
          key={f.name}
          className="flex items-center gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800 text-sm"
        >
          <File className="w-4 h-4 shrink-0 text-gray-400" />
          <div className="flex-1 min-w-0">
            <p className="truncate text-gray-700 dark:text-gray-300">{f.name}</p>
            {f.status === 'uploading' && (
              <div className="mt-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary-500 rounded-full transition-all"
                  style={{ width: `${f.progress}%` }}
                />
              </div>
            )}
            {f.status === 'error' && (
              <p className="text-red-500 text-xs mt-0.5">{f.error}</p>
            )}
          </div>
          {f.status === 'done' && (
            <CheckCircle className="w-4 h-4 text-green-500 shrink-0" />
          )}
          {f.status === 'error' && (
            <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
          )}
          {(f.status === 'done' || f.status === 'error') && (
            <button
              onClick={() => removeEntry(f.name)}
              aria-label="Dismiss"
              className="p-0.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      ))}
    </div>
  )
}
