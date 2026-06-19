import { Link } from "react-router-dom"
import { Product } from "@/types"
import { Card, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useAddToCart } from "@/hooks/useCart"
import { useAuthStore } from "@/store/useAuthStore"
import { useNavigate } from "react-router-dom"

import { formatPrice, getProductImageUrl } from "@/lib/utils"

interface ProductCardProps {
  product: Product
}

export function ProductCard({ product }: ProductCardProps) {
  const { mutate: addToCart, isPending } = useAddToCart()
  const { isAuthenticated } = useAuthStore()
  const navigate = useNavigate()

  const handleAddToCart = (e: React.MouseEvent) => {
    e.preventDefault()
    if (!isAuthenticated) {
      navigate("/login")
      return
    }
    addToCart({ product_id: product.id, quantity: 1 })
  }

  return (
    <Link to={`/products/${product.id}`}>
      <Card className="h-full flex flex-col overflow-hidden transition-all hover:shadow-md group">
        {/* Product Image */}
        <div className="aspect-square bg-muted relative overflow-hidden flex items-center justify-center">
          {product.image_url ? (
            <img 
              src={getProductImageUrl(product.image_url)} 
              alt={product.name}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <span className="text-muted-foreground text-sm font-medium">Image</span>
          )}
          {product.status !== 'active' || product.quantity === 0 ? (
            <div className="absolute top-2 right-2">
              <Badge variant="destructive">Out of Stock</Badge>
            </div>
          ) : (
            <div className="absolute top-2 right-2">
              <Badge variant="secondary" className="capitalize">{product.category}</Badge>
            </div>
          )}
        </div>
        
        <CardContent className="p-4 flex-1">
          <h3 className="font-semibold text-lg line-clamp-1 group-hover:text-primary transition-colors">
            {product.name}
          </h3>
          <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
            {product.description}
          </p>
          <div className="mt-2 flex items-center justify-between">
            <span className="font-bold text-lg text-primary">
              {formatPrice(product.price)}
            </span>
            <span className={`text-xs px-2 py-1 rounded-md font-medium ${
              product.quantity === 0 
                ? "bg-destructive/10 text-destructive" 
                : product.quantity <= 10 
                  ? "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400" 
                  : "bg-muted text-muted-foreground"
            }`}>
              {product.quantity === 0 ? "Out of stock" : `Stock: ${product.quantity}`}
            </span>
          </div>
        </CardContent>
        
        <CardFooter className="p-4 pt-0">
          <Button 
            className="w-full" 
            onClick={handleAddToCart}
            disabled={product.status !== 'active' || product.quantity === 0 || isPending}
          >
            {isPending ? "Adding..." : "Add to Cart"}
          </Button>
        </CardFooter>
      </Card>
    </Link>
  )
}
