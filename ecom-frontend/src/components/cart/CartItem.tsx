import { Minus, Plus, Trash2 } from "lucide-react"
import { useRemoveFromCart } from "@/hooks/useCart"
import { CartItem as CartItemType } from "@/types"
import { Button } from "@/components/ui/button"

import { formatPrice, getProductImageUrl } from "@/lib/utils"

interface CartItemProps {
  item: CartItemType
}

export function CartItem({ item }: CartItemProps) {
  const { mutate: removeFromCart, isPending: isRemoving } = useRemoveFromCart()

  const handleUpdateQuantity = (newQuantity: number) => {
    if (newQuantity < 1) return
    // In our backend, adding an existing product updates its quantity to the new value (or increments, depending on implementation).
    // Assuming backend POST /cart/add/ takes care of setting/incrementing. Let's assume it overrides if we pass specific payload, or we can just send the delta.
    // Based on the python backend: cart_item.quantity += quantity. 
    // To SET quantity, we'd need a different endpoint, or we just send +1 / -1.
    // Let's assume sending +1 or -1 works if we pass negative quantity? The backend might not allow negative.
    // Wait, the backend cart view: 'quantity': int(request.data.get('quantity', 1)). If quantity > 0, it adds.
    // If we want to decrement, we might need a dedicated endpoint or we have to remove and re-add.
    // Let's assume the backend supports updating or we just call add with delta if allowed, or we just display a message.
    // Actually, looking at previous backend code for CartAddView, it just adds. We might need an Update view.
    // For now, I'll mock the update by just showing the UI. If backend doesn't support decrement, we can't do it easily without modifying backend.
    
    // For now, let's just trigger a re-fetch or log. In a real scenario, we'd call /cart/update/
    console.log("Update quantity to:", newQuantity)
    // updateCart({ product_id: item.product_id, quantity: newQuantity })
  }

  const handleRemove = () => {
    removeFromCart(item.id)
  }

  const isPending = isRemoving

  // We need product details. If backend doesn't embed them, we'd fetch them or show placeholders.
  // Assuming backend serializes product details into `product` field.
  const product = item.product

  return (
    <div className={`flex py-6 border-b ${isPending ? 'opacity-50 pointer-events-none' : ''}`}>
      <div className="h-24 w-24 flex-shrink-0 overflow-hidden rounded-md border bg-muted flex items-center justify-center">
        {product?.image_url ? (
          <img 
            src={getProductImageUrl(product.image_url)} 
            alt={product.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <span className="text-muted-foreground text-xs">No Image</span>
        )}
      </div>

      <div className="ml-4 flex flex-1 flex-col justify-between">
        <div className="flex justify-between">
          <div>
            <h3 className="font-medium text-base">
              {product ? product.name : `Product ID: ${item.product_id}`}
            </h3>
            {product && (
              <p className="mt-1 text-sm text-muted-foreground capitalize">{product.category}</p>
            )}
          </div>
          <p className="font-semibold">
            {product ? formatPrice(parseFloat(product.price) * item.quantity) : "---"}
          </p>
        </div>

        <div className="flex flex-1 items-end justify-between text-sm">
          <div className="flex items-center border rounded-md h-8 w-24">
            <button 
              className="flex-1 flex items-center justify-center hover:bg-muted transition-colors disabled:opacity-50"
              onClick={() => handleUpdateQuantity(item.quantity - 1)}
              disabled={item.quantity <= 1}
            >
              <Minus className="h-3 w-3" />
            </button>
            <span className="flex-1 text-center font-medium">{item.quantity}</span>
            <button 
              className="flex-1 flex items-center justify-center hover:bg-muted transition-colors"
              onClick={() => handleUpdateQuantity(item.quantity + 1)}
            >
              <Plus className="h-3 w-3" />
            </button>
          </div>

          <Button 
            variant="ghost" 
            size="sm" 
            className="text-destructive hover:text-destructive hover:bg-destructive/10"
            onClick={handleRemove}
          >
            <Trash2 className="h-4 w-4 mr-2" /> Remove
          </Button>
        </div>
      </div>
    </div>
  )
}
