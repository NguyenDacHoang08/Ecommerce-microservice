import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { CheckCircle2, ArrowRight, Package } from "lucide-react"

import { Button } from "@/components/ui/button"
import { useCheckoutStore } from "@/store/useCheckoutStore"

export default function OrderSuccess() {
  const { orderId, resetCheckout } = useCheckoutStore()
  const [savedOrderId] = useState(orderId)
  const navigate = useNavigate()

  useEffect(() => {
    // If user somehow gets here without an orderId (e.g., direct URL access), redirect them
    if (!savedOrderId) {
      navigate("/")
    }
  }, [savedOrderId, navigate])

  useEffect(() => {
    // Cleanup checkout state when they leave this page
    return () => {
      resetCheckout()
    }
  }, [resetCheckout])

  if (!savedOrderId) return null

  return (
    <div className="container py-24 flex flex-col items-center justify-center text-center max-w-2xl">
      <div className="h-24 w-24 bg-green-100 text-green-600 rounded-full flex items-center justify-center mb-8">
        <CheckCircle2 className="h-12 w-12" />
      </div>
      
      <h1 className="text-4xl font-extrabold tracking-tight mb-4">Payment Successful!</h1>
      <p className="text-xl text-muted-foreground mb-8">
        Thank you for your purchase. Your order has been placed and is being processed.
      </p>

      <div className="bg-muted/50 w-full rounded-xl p-6 mb-8 border flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-4 text-left">
          <div className="p-3 bg-background rounded-full shadow-sm">
            <Package className="h-6 w-6 text-primary" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Order ID</p>
            <p className="font-bold text-lg font-mono">{savedOrderId}</p>
          </div>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
        <Button onClick={() => navigate("/profile")} variant="outline" className="h-12 px-8">
          View Order History
        </Button>
        <Button onClick={() => navigate("/products")} className="h-12 px-8">
          Continue Shopping <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
