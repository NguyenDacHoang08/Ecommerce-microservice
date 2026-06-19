import { useParams, useNavigate } from "react-router-dom"
import { useState } from "react"
import { useProductDetail } from "@/hooks/useProducts"
import { useAddToCart } from "@/hooks/useCart"
import { useAuthStore } from "@/store/useAuthStore"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { ShoppingCart, Minus, Plus, ArrowLeft } from "lucide-react"

import { formatPrice, getProductImageUrl } from "@/lib/utils"

export default function ProductDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { isAuthenticated } = useAuthStore()
  
  const { data: product, isLoading, isError } = useProductDetail(id || "")
  const { mutate: addToCart, isPending } = useAddToCart()
  
  const [quantity, setQuantity] = useState(1)
  const [activeImageIdx, setActiveImageIdx] = useState(0)

  const handleQuantityChange = (delta: number) => {
    if (!product) return
    const newQuantity = quantity + delta
    if (newQuantity >= 1 && newQuantity <= product.quantity) {
      setQuantity(newQuantity)
    }
  }

  const handleAddToCart = () => {
    if (!product) return
    if (!isAuthenticated) {
      navigate("/login")
      return
    }
    addToCart({ product_id: product.id, quantity })
  }

  if (isLoading) {
    return (
      <div className="container py-8 flex flex-col md:flex-row gap-8">
        <Skeleton className="w-full md:w-1/2 aspect-square rounded-xl" />
        <div className="w-full md:w-1/2 space-y-4">
          <Skeleton className="h-10 w-3/4" />
          <Skeleton className="h-6 w-1/4" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-12 w-1/3" />
        </div>
      </div>
    )
  }

  if (isError || !product) {
    return (
      <div className="container py-16 text-center">
        <h2 className="text-2xl font-bold text-destructive">Product not found</h2>
        <Button variant="outline" className="mt-4" onClick={() => navigate("/products")}>
          Back to Products
        </Button>
      </div>
    )
  }

  return (
    <div className="container py-8">
      <button 
        onClick={() => navigate(-1)} 
        className="flex items-center text-sm text-muted-foreground hover:text-foreground mb-6 transition-colors"
      >
        <ArrowLeft className="mr-2 h-4 w-4" /> Back
      </button>
 
      <div className="flex flex-col md:flex-row gap-12">
        {/* Product Images */}
        <div className="w-full md:w-1/2 space-y-4">
          {product.images && product.images.length > 0 ? (
            <>
              {/* Main Image */}
              <div className="aspect-square bg-muted rounded-xl overflow-hidden border relative flex items-center justify-center">
                <img
                  src={getProductImageUrl(product.images[activeImageIdx]?.url)}
                  alt={product.images[activeImageIdx]?.alt_text || product.name}
                  className="w-full h-full object-cover"
                />
              </div>

              {/* Thumbnails */}
              {product.images.length > 1 && (
                <div className="flex gap-2 overflow-x-auto pb-2">
                  {product.images.map((img, idx) => (
                    <button
                      key={img.id || idx}
                      type="button"
                      onClick={() => setActiveImageIdx(idx)}
                      className={`w-16 h-16 rounded-lg overflow-hidden border-2 shrink-0 ${
                        activeImageIdx === idx ? "border-primary" : "border-transparent"
                      }`}
                    >
                      <img src={getProductImageUrl(img.url)} alt="" className="w-full h-full object-cover" />
                    </button>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div className="aspect-square bg-muted rounded-xl flex items-center justify-center text-muted-foreground border">
              No Image Available
            </div>
          )}
        </div>
 
        {/* Product Info */}
        <div className="w-full md:w-1/2 flex flex-col">
          <div className="mb-2">
            <Badge variant="secondary" className="capitalize">{product.category}</Badge>
          </div>
          
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight mb-4">{product.name}</h1>
          
          <div className="text-3xl font-bold text-primary mb-6">
            {formatPrice(product.price)}
          </div>
          
          <p className="text-muted-foreground text-base mb-8 whitespace-pre-wrap">
            {product.description}
          </p>

          {/* Specific Fields based on Category */}
          <div className="bg-muted/30 rounded-lg p-4 mb-8 space-y-2 text-sm">
            {product.brand && (
              <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground">Brand</span>
                <span className="font-medium">{product.brand}</span>
              </div>
            )}
            {product.author && (
              <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground">Author</span>
                <span className="font-medium">{product.author}</span>
              </div>
            )}
            {product.size && (
              <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground">Size</span>
                <span className="font-medium">{product.size}</span>
              </div>
            )}
            {product.color && (
              <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground">Color</span>
                <span className="font-medium capitalize">{product.color}</span>
              </div>
            )}
            <div className="flex justify-between pt-2">
              <span className="text-muted-foreground">Availability</span>
              <span className={`font-medium ${product.quantity > 0 ? "text-green-600" : "text-destructive"}`}>
                {product.quantity > 0 ? `${product.quantity} in stock` : "Out of stock"}
              </span>
            </div>
          </div>

          {/* Add to Cart Actions */}
          {product.status === 'active' && product.quantity > 0 ? (
            <div className="flex flex-col sm:flex-row gap-4 mt-auto">
              <div className="flex items-center border rounded-md h-12 w-32">
                <button 
                  className="flex-1 flex items-center justify-center hover:bg-muted transition-colors disabled:opacity-50"
                  onClick={() => handleQuantityChange(-1)}
                  disabled={quantity <= 1}
                >
                  <Minus className="h-4 w-4" />
                </button>
                <span className="flex-1 text-center font-medium">{quantity}</span>
                <button 
                  className="flex-1 flex items-center justify-center hover:bg-muted transition-colors disabled:opacity-50"
                  onClick={() => handleQuantityChange(1)}
                  disabled={quantity >= product.quantity}
                >
                  <Plus className="h-4 w-4" />
                </button>
              </div>
              
              <Button 
                className="flex-1 h-12 text-base" 
                onClick={handleAddToCart}
                disabled={isPending}
              >
                <ShoppingCart className="mr-2 h-5 w-5" />
                {isPending ? "Adding..." : "Add to Cart"}
              </Button>
            </div>
          ) : (
            <div className="mt-auto p-4 bg-destructive/10 text-destructive text-center rounded-md font-medium">
              This product is currently unavailable.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
