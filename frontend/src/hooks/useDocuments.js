/**
 * React Query hooks for document management.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { deleteDocument, getDocuments, uploadDocument } from '../services/api'

const DOCS_KEY = ['documents']

/** Fetch all documents. */
export function useDocuments() {
  return useQuery({
    queryKey: DOCS_KEY,
    queryFn: getDocuments,
    select: (data) => data.documents ?? [],
  })
}

/** Upload a PDF. */
export function useUploadDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ file, onProgress }) => uploadDocument(file, onProgress),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: DOCS_KEY })
      toast.success(`"${data.filename}" uploaded successfully (${data.chunk_count} chunks)`)
    },
    onError: (err) => {
      toast.error(`Upload failed: ${err.message}`)
    },
  })
}

/** Delete a document. */
export function useDeleteDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (docId) => deleteDocument(docId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DOCS_KEY })
      toast.success('Document deleted')
    },
    onError: (err) => {
      toast.error(`Delete failed: ${err.message}`)
    },
  })
}
