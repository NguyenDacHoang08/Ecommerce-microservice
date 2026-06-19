import { Link } from "react-router-dom"
import { Sparkles, TrendingUp, ShoppingCart, Star, Zap, RefreshCw, Lock } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { useAuthStore } from "@/store/useAuthStore"
import { useRecommendations, RecommendedProduct } from "@/hooks/useRecommendations"
import { useAddToCart } from "@/hooks/useCart"
import { useNavigate } from "react-router-dom"
import { formatPrice, getProductImageUrl } from "@/lib/utils"

// ── Recommendation Card ────────────────────────────────────────────────────────
function RecommendCard({ product, rank }: { product: RecommendedProduct; rank: number }) {
  const { mutate: addToCart, isPending } = useAddToCart()
  const { isAuthenticated } = useAuthStore()
  const navigate = useNavigate()

  const handleAddToCart = (e: React.MouseEvent) => {
    e.preventDefault()
    if (!isAuthenticated) { navigate("/login"); return }
    addToCart({ product_id: product.product_id, quantity: 1 })
  }

  const scorePercent = Math.round(product.score * 100)

  return (
    <Link to={`/products/${product.product_id}`} className="group block h-full">
      <div className="relative rounded-2xl border bg-card text-card-foreground shadow-sm overflow-hidden transition-all duration-300 hover:shadow-xl hover:-translate-y-1 flex flex-col h-full">
        {/* Rank Badge */}
        <div className="absolute top-3 left-3 z-10">
          <span className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold shadow-md
            ${rank === 1 ? "bg-yellow-400 text-yellow-900" :
              rank === 2 ? "bg-slate-300 text-slate-800" :
              rank === 3 ? "bg-amber-600 text-white" :
              "bg-primary/80 text-primary-foreground"}`}>
            {rank}
          </span>
        </div>

        {/* AI Score */}
        <div className="absolute top-3 right-3 z-10">
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-primary/90 text-primary-foreground text-[11px] font-semibold shadow">
            <Sparkles className="h-3 w-3" />
            {scorePercent}%
          </span>
        </div>

        {/* Image */}
        <div className="aspect-square bg-muted relative overflow-hidden">
          {product.image_url ? (
            <img
              src={getProductImageUrl(product.image_url)}
              alt={product.name}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            />
          ) : (
            <div className="w-full h-full flex flex-col items-center justify-center gap-2 bg-gradient-to-br from-primary/5 to-primary/20">
              <Sparkles className="h-10 w-10 text-primary/40" />
              <span className="text-xs text-muted-foreground font-mono">#{product.product_id}</span>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="p-4 flex-1 flex flex-col gap-2">
          {product.category && (
            <Badge variant="secondary" className="w-fit capitalize text-xs">{product.category}</Badge>
          )}

          <h3 className="font-semibold text-base line-clamp-2 group-hover:text-primary transition-colors leading-snug">
            {product.name || `Sản phẩm #${product.product_id}`}
          </h3>

          {product.description && (
            <p className="text-xs text-muted-foreground line-clamp-2 flex-1">{product.description}</p>
          )}

          {/* Score breakdown */}
          {(product.lstm_score != null || product.graph_score != null || product.rag_score != null) && (
            <div className="flex gap-2 flex-wrap mt-1">
              {product.lstm_score != null && (
                <span className="text-[10px] bg-blue-500/10 text-blue-600 dark:text-blue-400 px-1.5 py-0.5 rounded font-mono">
                  LSTM {Math.round(product.lstm_score * 100)}%
                </span>
              )}
              {product.graph_score != null && (
                <span className="text-[10px] bg-purple-500/10 text-purple-600 dark:text-purple-400 px-1.5 py-0.5 rounded font-mono">
                  Graph {Math.round(product.graph_score * 100)}%
                </span>
              )}
              {product.rag_score != null && (
                <span className="text-[10px] bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-1.5 py-0.5 rounded font-mono">
                  RAG {Math.round(product.rag_score * 100)}%
                </span>
              )}
            </div>
          )}

          <div className="mt-auto pt-1">
            {product.price != null ? (
              <span className="font-bold text-lg text-primary">{formatPrice(product.price)}</span>
            ) : (
              <span className="text-sm text-muted-foreground">Xem giá</span>
            )}
          </div>
        </div>

        <div className="px-4 pb-4">
          <Button className="w-full gap-2" size="sm" onClick={handleAddToCart} disabled={isPending}>
            <ShoppingCart className="h-4 w-4" />
            {isPending ? "Đang thêm..." : "Thêm vào giỏ"}
          </Button>
        </div>
      </div>
    </Link>
  )
}

function RecommendSkeleton() {
  return (
    <div className="rounded-2xl border bg-card shadow-sm overflow-hidden">
      <Skeleton className="aspect-square w-full" />
      <div className="p-4 space-y-3">
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-5 w-full" />
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-9 w-full mt-2" />
      </div>
    </div>
  )
}

// ── Guest CTA ──────────────────────────────────────────────────────────────────
function GuestPrompt() {
  return (
    <div className="py-16 text-center space-y-6">
      <div className="flex justify-center">
        <div className="w-24 h-24 rounded-full bg-primary/10 flex items-center justify-center">
          <Lock className="h-12 w-12 text-primary/50" />
        </div>
      </div>
      <div className="space-y-2">
        <h3 className="text-2xl font-bold">Cần đăng nhập để xem gợi ý</h3>
        <p className="text-muted-foreground max-w-md mx-auto">
          AI của chúng tôi sẽ phân tích hành vi mua sắm của bạn và gợi ý những sản phẩm phù hợp nhất.
        </p>
      </div>
      <div className="flex gap-3 justify-center flex-wrap">
        <Link to="/login">
          <Button className="gap-2 shadow-lg" size="lg">
            <Star className="h-4 w-4" />
            Đăng nhập ngay
          </Button>
        </Link>
        <Link to="/products">
          <Button variant="outline" size="lg" className="gap-2">
            <ShoppingCart className="h-4 w-4" />
            Xem tất cả sản phẩm
          </Button>
        </Link>
      </div>

      {/* Fake skeleton preview */}
      <div className="mt-8 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 opacity-30 pointer-events-none select-none">
        {Array.from({ length: 4 }).map((_, i) => <RecommendSkeleton key={i} />)}
      </div>
    </div>
  )
}

// ── Main Page ──────────────────────────────────────────────────────────────────
export default function Recommendations() {
  const { isAuthenticated, user } = useAuthStore()
  const { data: recommendations = [], isLoading, isError, refetch } = useRecommendations(
    isAuthenticated ? user?.id : null,
    12
  )

  return (
    <div className="container py-10 space-y-10">
      {/* Hero Header */}
      <div className="relative rounded-3xl overflow-hidden bg-gradient-to-br from-primary/10 via-primary/5 to-background border p-8 md:p-12">
        <div className="absolute -top-10 -right-10 w-48 h-48 rounded-full bg-primary/10 blur-3xl pointer-events-none" />
        <div className="absolute -bottom-10 -left-10 w-64 h-64 rounded-full bg-primary/5 blur-3xl pointer-events-none" />

        <div className="relative flex flex-col md:flex-row md:items-center gap-6 justify-between">
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-primary font-semibold text-sm uppercase tracking-wider">
              <Sparkles className="h-4 w-4" />
              AI-Powered · Hybrid Engine
            </div>
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight">
              Sản phẩm gợi ý cho bạn
            </h1>
            <p className="text-muted-foreground max-w-lg text-base">
              {isAuthenticated
                ? "Được phân tích từ lịch sử mua sắm của bạn bằng LSTM · Neo4j Graph · RAG Semantic Search."
                : "Đăng nhập để nhận gợi ý sản phẩm được cá nhân hoá bởi AI."}
            </p>

            <div className="flex items-center gap-4 flex-wrap text-xs text-muted-foreground pt-1">
              <span className="flex items-center gap-1"><Zap className="h-3 w-3 text-blue-500" /> LSTM 40%</span>
              <span className="flex items-center gap-1"><Zap className="h-3 w-3 text-purple-500" /> Graph 30%</span>
              <span className="flex items-center gap-1"><Zap className="h-3 w-3 text-emerald-500" /> RAG 30%</span>
            </div>
          </div>

          {isAuthenticated && (
            <Button
              variant="outline"
              size="icon"
              onClick={() => refetch()}
              disabled={isLoading}
              title="Làm mới gợi ý"
              className="rounded-full flex-shrink-0"
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            </Button>
          )}
        </div>
      </div>

      {/* Stats bar */}
      {isAuthenticated && !isLoading && !isError && recommendations.length > 0 && (
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-2 px-4 py-2 rounded-full border bg-primary text-primary-foreground text-sm font-medium">
            <TrendingUp className="h-4 w-4" />
            Cá nhân hoá
          </div>
          <span className="text-sm text-muted-foreground">
            {recommendations.length} sản phẩm được gợi ý
          </span>
        </div>
      )}

      {/* Content */}
      {!isAuthenticated ? (
        <GuestPrompt />
      ) : isError ? (
        <div className="p-8 text-center bg-destructive/10 text-destructive rounded-2xl border border-destructive/20 space-y-3">
          <p className="font-semibold">Không thể tải gợi ý sản phẩm.</p>
          <p className="text-sm opacity-80">AI service có thể chưa sẵn sàng hoặc bạn chưa có lịch sử mua sắm.</p>
          <Button variant="outline" size="sm" onClick={() => refetch()} className="mt-2">
            <RefreshCw className="h-4 w-4 mr-2" /> Thử lại
          </Button>
        </div>
      ) : isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {Array.from({ length: 8 }).map((_, i) => <RecommendSkeleton key={i} />)}
        </div>
      ) : recommendations.length === 0 ? (
        <div className="py-20 text-center space-y-4">
          <div className="flex justify-center">
            <div className="w-20 h-20 rounded-full bg-muted flex items-center justify-center">
              <Sparkles className="h-10 w-10 text-muted-foreground" />
            </div>
          </div>
          <h3 className="text-xl font-semibold">Chưa có gợi ý nào</h3>
          <p className="text-muted-foreground max-w-sm mx-auto text-sm">
            AI cần thêm dữ liệu hành vi của bạn. Hãy xem và mua thêm sản phẩm để nhận gợi ý.
          </p>
          <Link to="/products">
            <Button className="mt-2 gap-2">
              <ShoppingCart className="h-4 w-4" />
              Khám phá sản phẩm
            </Button>
          </Link>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {recommendations.map((product, index) => (
              <RecommendCard key={product.product_id} product={product} rank={index + 1} />
            ))}
          </div>

          <div className="text-center pt-6 border-t">
            <p className="text-muted-foreground text-sm mb-4">Muốn xem thêm sản phẩm khác?</p>
            <Link to="/products">
              <Button variant="outline" className="gap-2">
                <ShoppingCart className="h-4 w-4" />
                Xem tất cả sản phẩm
              </Button>
            </Link>
          </div>
        </>
      )}
    </div>
  )
}
