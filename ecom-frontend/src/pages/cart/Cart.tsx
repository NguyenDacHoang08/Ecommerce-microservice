import { useCart, useClearCart } from "@/hooks/useCart"
import { CartItem as CartItemComponent } from "@/components/cart/CartItem"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { ShoppingBag, ArrowRight, Trash2 } from "lucide-react"
import { Link, useNavigate } from "react-router-dom"
import { formatPrice } from "@/lib/utils"

export default function Cart() {
  const { data: cart, isLoading, isError } = useCart()
  const { mutate: clearCart, isPending: isClearing } = useClearCart()
  const navigate = useNavigate()

  // Calculate total safely assuming product exists. 
  // If backend returns detailed product, we multiply. If not, we might not be able to calculate here.
  const calculateTotal = () => {
    if (!cart?.items) return 0
    return cart.items.reduce((total, item) => {
      if (item.product && item.product.price) {
        return total + (parseFloat(item.product.price) * item.quantity)
      }
      return total
    }, 0)
  }

  const subtotal = calculateTotal()
  const shipping = subtotal > 0 ? 30000 : 0 // flat rate shipping for demo: 30,000 VND
  const total = subtotal + shipping

  if (isLoading) {
    return (
      <div className="container py-12 flex flex-col lg:flex-row gap-8">
        <div className="flex-1 space-y-6">
          <Skeleton className="h-8 w-48 mb-6" />
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-32 w-full rounded-lg" />
          ))}
        </div>
        <div className="w-full lg:w-96">
          <Skeleton className="h-64 w-full rounded-xl" />
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="container py-24 text-center">
        <h2 className="text-2xl font-bold text-destructive mb-4">Failed to load cart</h2>
        <Button onClick={() => window.location.reload()}>Try Again</Button>
      </div>
    )
  }

  const isEmpty = !cart?.items || cart.items.length === 0

  if (isEmpty) {
    return (
      <div className="container py-24 flex flex-col items-center justify-center text-center">
        <div className="h-24 w-24 bg-muted rounded-full flex items-center justify-center mb-6">
          <ShoppingBag className="h-10 w-10 text-muted-foreground" />
        </div>
        <h2 className="text-3xl font-extrabold tracking-tight mb-2">Your cart is empty</h2>
        <p className="text-muted-foreground mb-8 max-w-md">
          Looks like you haven't added anything to your cart yet. Discover our amazing products and start shopping.
        </p>
        <Link to="/products">
          <Button size="lg">Start Shopping</Button>
        </Link>
      </div>
    )
  }

  return (
    <div className="container py-12">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-extrabold tracking-tight">Shopping Cart</h1>
        <Button 
          variant="outline" 
          className="text-destructive hover:bg-destructive/10 hover:text-destructive"
          onClick={() => clearCart()}
          disabled={isClearing}
        >
          <Trash2 className="h-4 w-4 mr-2" /> Clear Cart
        </Button>
      </div>

      <div className="flex flex-col lg:flex-row gap-12">
        {/* Cart Items List */}
        <div className="flex-1 border-t">
          {cart.items.map((item) => (
            <CartItemComponent key={item.id} item={item} />
          ))}
        </div>

        {/* Order Summary */}
        <div className="w-full lg:w-96 shrink-0">
          <Card className="sticky top-24">
            <CardHeader>
              <CardTitle>Order Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Subtotal</span>
                <span className="font-medium">{formatPrice(subtotal)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Shipping estimate</span>
                <span className="font-medium">{formatPrice(shipping)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Tax estimate</span>
                <span className="font-medium">Calculated at checkout</span>
              </div>
              <div className="border-t pt-4 mt-4 flex justify-between">
                <span className="font-bold text-lg">Order Total</span>
                <span className="font-bold text-lg">{formatPrice(total)}</span>
              </div>
            </CardContent>
            <CardFooter>
              <Button 
                className="w-full h-12 text-base" 
                onClick={() => navigate('/checkout')}
              >
                Proceed to Checkout <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </CardFooter>
          </Card>
        </div>
      </div>
    </div>
  )
}
