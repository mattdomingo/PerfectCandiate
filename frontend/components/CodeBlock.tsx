import { useState } from 'react'
import { ClipboardIcon, CheckIcon } from '@heroicons/react/24/outline'

interface CodeBlockProps {
  children: string
  language?: string
  title?: string
}

export default function CodeBlock({ children, language = 'text', title }: CodeBlockProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(children)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  return (
    <div className="relative group">
      {title && (
        <div className="bg-gray-800 text-gray-200 px-4 py-2 text-sm font-medium rounded-t-lg border-b border-gray-700">
          {title}
        </div>
      )}
      <div className="relative">
        <pre className={`bg-gray-900 text-gray-100 p-4 overflow-x-auto text-sm ${title ? 'rounded-t-none' : ''} rounded-lg`}>
          <code className={`language-${language}`}>{children}</code>
        </pre>
        <button
          onClick={handleCopy}
          className="absolute top-2 right-2 p-2 text-gray-400 hover:text-gray-200 transition-colors opacity-0 group-hover:opacity-100"
          title="Copy to clipboard"
        >
          {copied ? (
            <CheckIcon className="w-4 h-4 text-green-400" />
          ) : (
            <ClipboardIcon className="w-4 h-4" />
          )}
        </button>
      </div>
    </div>
  )
}


