import { useState, useRef, useEffect } from 'react'
import { MessageCircle, X, Send, Bot, User, Loader2, ShoppingCart, Sparkles, ExternalLink } from 'lucide-react'
import { Link } from 'react-router-dom'
import { apiClient } from '@/lib/axios'
import { formatPrice, getProductImageUrl } from '@/lib/utils'

// ── Types ──────────────────────────────────────────────────────────────────────
interface ProductRef {
  id: string | null
  name: string | null
  price: number | null
  category: string | null
  score: number | null
  image_url: string | null
}

interface ChatMessage {
  role: 'user' | 'bot'
  text: string
  products?: ProductRef[]
  source?: string
  timestamp: Date
}

// ── Product chip inside chat ───────────────────────────────────────────────────
function ProductChip({ product }: { product: ProductRef }) {
  if (!product.id) return null
  return (
    <Link
      to={`/products/${product.id}`}
      className="flex items-center gap-2 p-2 rounded-lg border bg-background hover:bg-accent transition-colors group mt-1"
    >
      <div className="w-10 h-10 rounded-md bg-muted overflow-hidden flex-shrink-0">
        {product.image_url ? (
          <img
            src={getProductImageUrl(product.image_url)}
            alt={product.name || ''}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <ShoppingCart className="h-4 w-4 text-muted-foreground" />
          </div>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium line-clamp-1 group-hover:text-primary transition-colors">
          {product.name}
        </p>
        {product.price != null && (
          <p className="text-xs text-primary font-semibold">{formatPrice(product.price)}</p>
        )}
      </div>
      <ExternalLink className="h-3 w-3 text-muted-foreground flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
    </Link>
  )
}

// ── Suggested questions ────────────────────────────────────────────────────────
const SUGGESTIONS = [
  'Laptop gaming giá tốt',
  'Sách lập trình hay nhất',
  'Giày thể thao Nike',
  'Tai nghe chống ồn tốt',
  'Đồng hồ thông minh',
]

// ── Main Chatbot Component ─────────────────────────────────────────────────────
export default function ChatBot() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'bot',
      text: 'Xin chào! 👋 Tôi là trợ lý mua sắm AI. Bạn cần tìm sản phẩm gì hôm nay?',
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [hasNew, setHasNew] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Auto scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setHasNew(false)
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [isOpen])

  const sendMessage = async (question: string) => {
    if (!question.trim() || isLoading) return

    const userMsg: ChatMessage = {
      role: 'user',
      text: question.trim(),
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setIsLoading(true)

    try {
      const { data } = await apiClient.post('/chatbot', {
        question: question.trim(),
        top_k: 5,
      })

      const botMsg: ChatMessage = {
        role: 'bot',
        text: data.answer,
        products: data.products?.filter((p: ProductRef) => p.id) ?? [],
        source: data.source,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, botMsg])

      if (!isOpen) setHasNew(true)
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          role: 'bot',
          text: 'Xin lỗi, tôi đang gặp sự cố. Vui lòng thử lại sau ít phút nhé! 🙏',
          timestamp: new Date(),
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    sendMessage(input)
  }

  const handleSuggestion = (text: string) => {
    sendMessage(text)
  }

  const formatTime = (d: Date) =>
    d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })

  return (
    <>
      {/* ── Floating Button ── */}
      <button
        id="chatbot-toggle"
        onClick={() => setIsOpen(o => !o)}
        className={`fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full shadow-lg flex items-center justify-center transition-all duration-300
          ${isOpen
            ? 'bg-destructive text-destructive-foreground rotate-0 scale-100'
            : 'bg-primary text-primary-foreground hover:scale-110'
          }`}
        aria-label="Open chatbot"
      >
        {isOpen ? (
          <X className="h-6 w-6" />
        ) : (
          <>
            <MessageCircle className="h-6 w-6" />
            {hasNew && (
              <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-red-500 flex items-center justify-center">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                <span className="relative h-2 w-2 rounded-full bg-red-500" />
              </span>
            )}
          </>
        )}
      </button>

      {/* ── Chat Window ── */}
      <div
        className={`fixed bottom-24 right-6 z-50 w-[360px] max-w-[calc(100vw-24px)] rounded-2xl border bg-background shadow-2xl flex flex-col transition-all duration-300 origin-bottom-right
          ${isOpen ? 'opacity-100 scale-100 pointer-events-auto' : 'opacity-0 scale-95 pointer-events-none'}`}
        style={{ height: '520px' }}
      >
        {/* Header */}
        <div className="flex items-center gap-3 p-4 border-b bg-primary text-primary-foreground rounded-t-2xl flex-shrink-0">
          <div className="relative">
            <div className="w-9 h-9 rounded-full bg-primary-foreground/20 flex items-center justify-center">
              <Bot className="h-5 w-5" />
            </div>
            <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-400 border-2 border-primary rounded-full" />
          </div>
          <div className="flex-1">
            <p className="font-semibold text-sm">AI Shopping Assistant</p>
            <p className="text-xs text-primary-foreground/70 flex items-center gap-1">
              <Sparkles className="h-3 w-3" /> Powered by RAG · FAISS
            </p>
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1.5 rounded-full hover:bg-primary-foreground/20 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              {/* Avatar */}
              <div className={`w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold
                ${msg.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground'}`}
              >
                {msg.role === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
              </div>

              <div className={`flex flex-col gap-1 max-w-[78%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                {/* Bubble */}
                <div className={`px-3 py-2 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap
                  ${msg.role === 'user'
                    ? 'bg-primary text-primary-foreground rounded-tr-sm'
                    : 'bg-muted text-foreground rounded-tl-sm'}`}
                >
                  {msg.text}
                </div>

                {/* Product chips */}
                {msg.products && msg.products.length > 0 && (
                  <div className="w-full space-y-1 mt-1">
                    <p className="text-xs text-muted-foreground px-1">Sản phẩm liên quan:</p>
                    {msg.products.slice(0, 4).map((p, pi) => (
                      <ProductChip key={pi} product={p} />
                    ))}
                  </div>
                )}

                {/* Timestamp + source */}
                <span className="text-[10px] text-muted-foreground px-1">
                  {formatTime(msg.timestamp)}
                  {msg.source && msg.source !== 'template' && (
                    <span className="ml-1 opacity-60">· {msg.source}</span>
                  )}
                </span>
              </div>
            </div>
          ))}

          {/* Loading indicator */}
          {isLoading && (
            <div className="flex gap-2 items-start">
              <div className="w-7 h-7 rounded-full bg-muted flex items-center justify-center flex-shrink-0">
                <Bot className="h-4 w-4 text-muted-foreground" />
              </div>
              <div className="px-3 py-2 rounded-2xl rounded-tl-sm bg-muted">
                <div className="flex gap-1 items-center h-5">
                  <span className="w-1.5 h-1.5 bg-muted-foreground/60 rounded-full animate-bounce [animation-delay:0ms]" />
                  <span className="w-1.5 h-1.5 bg-muted-foreground/60 rounded-full animate-bounce [animation-delay:150ms]" />
                  <span className="w-1.5 h-1.5 bg-muted-foreground/60 rounded-full animate-bounce [animation-delay:300ms]" />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggestions (show only on first message) */}
        {messages.length === 1 && !isLoading && (
          <div className="px-4 pb-2 flex-shrink-0">
            <p className="text-xs text-muted-foreground mb-2">Gợi ý câu hỏi:</p>
            <div className="flex flex-wrap gap-1.5">
              {SUGGESTIONS.map(s => (
                <button
                  key={s}
                  onClick={() => handleSuggestion(s)}
                  className="text-xs px-2.5 py-1 rounded-full border border-primary/30 text-primary hover:bg-primary hover:text-primary-foreground transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <form
          onSubmit={handleSubmit}
          className="p-3 border-t flex gap-2 items-center flex-shrink-0"
        >
          <input
            ref={inputRef}
            id="chatbot-input"
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Nhập câu hỏi của bạn..."
            disabled={isLoading}
            className="flex-1 h-9 rounded-full border border-input bg-muted px-4 text-sm outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-all disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            id="chatbot-send"
            className="w-9 h-9 rounded-full bg-primary text-primary-foreground flex items-center justify-center flex-shrink-0 hover:opacity-90 transition-opacity disabled:opacity-40"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </button>
        </form>
      </div>
    </>
  )
}
