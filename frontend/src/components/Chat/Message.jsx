import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const markdownComponents = {
  p: ({ children }) => <p className="mb-3 leading-7 last:mb-0">{children}</p>,
  ul: ({ children }) => <ul className="mb-3 list-disc space-y-1 pl-5 last:mb-0">{children}</ul>,
  ol: ({ children }) => <ol className="mb-3 list-decimal space-y-1 pl-5 last:mb-0">{children}</ol>,
  li: ({ children }) => <li className="leading-7">{children}</li>,
  a: ({ children, href }) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-accent underline decoration-accent/40 underline-offset-2 hover:decoration-accent"
    >
      {children}
    </a>
  ),
  strong: ({ children }) => <strong className="font-semibold text-text">{children}</strong>,
  h1: ({ children }) => <h3 className="mb-2 mt-4 text-base font-semibold text-text first:mt-0">{children}</h3>,
  h2: ({ children }) => <h3 className="mb-2 mt-4 text-base font-semibold text-text first:mt-0">{children}</h3>,
  h3: ({ children }) => <h3 className="mb-2 mt-4 text-[15px] font-semibold text-text first:mt-0">{children}</h3>,
  blockquote: ({ children }) => (
    <blockquote className="mb-3 border-l-2 border-border pl-3 text-text-muted last:mb-0">{children}</blockquote>
  ),
  code: ({ className, children, node }) => {
    const language = /language-(\w+)/.exec(className || '')?.[1]
    // react-markdown no longer passes an `inline` flag; a fenced code block
    // either carries a `language-*` class or spans multiple source lines,
    // while true inline code is always a single line with no language class.
    const isBlock = Boolean(language) || node?.position?.start.line !== node?.position?.end.line
    if (!isBlock) {
      return (
        <code className="rounded bg-surface-2 px-1.5 py-0.5 font-mono text-[0.85em] text-accent-text">
          {children}
        </code>
      )
    }
    return (
      <div className="mb-3 overflow-hidden rounded-xl border border-border-soft bg-[#141317] last:mb-0">
        {language && (
          <div className="border-b border-border-soft px-3.5 py-1.5 font-mono text-xs text-text-faint">
            {language}
          </div>
        )}
        <pre className="overflow-x-auto px-3.5 py-3 text-[13px] leading-6">
          <code className="font-mono text-text">{children}</code>
        </pre>
      </div>
    )
  },
}

export function Message({ role, text }) {
  const isUser = role === 'user'

  if (isUser) {
    return (
      <div className="animate-rise flex justify-end">
        <div className="max-w-[85%] whitespace-pre-wrap break-words rounded-2xl rounded-tr-sm border border-accent/15 bg-accent-muted px-4 py-2.5 text-[15px] leading-7 text-text sm:max-w-[75%]">
          {text}
        </div>
      </div>
    )
  }

  return (
    <div className="animate-rise flex justify-start">
      <div className="max-w-full text-[15px] text-text">
        <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
          {text}
        </ReactMarkdown>
      </div>
    </div>
  )
}
