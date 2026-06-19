import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { Check } from "lucide-react"

import { useCart } from "@/hooks/useCart"
import { useCreateOrder, useProcessPayment } from "@/hooks/useCheckoutApi"
import { useCheckoutStore } from "@/store/useCheckoutStore"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"

import { formatPrice } from "@/lib/utils"

const shippingSchema = z.object({
  fullName: z.string().min(2, "Full name is required"),
  phone: z.string().min(10, "Valid phone number is required"),
  addressLine: z.string().min(5, "Address is required"),
  city: z.string().min(2, "City is required"),
  country: z.string().min(2, "Country is required"),
})

export default function Checkout() {
  const navigate = useNavigate()
  const { data: cart, isLoading: isCartLoading } = useCart()
  const { currentStep, nextStep, prevStep, shippingAddress, setShippingAddress, paymentMethod, setPaymentMethod, setOrderId } = useCheckoutStore()
  
  const { mutateAsync: createOrder, isPending: isCreatingOrder } = useCreateOrder()
  const { mutateAsync: processPayment, isPending: isProcessingPayment } = useProcessPayment()

  const [checkoutError, setCheckoutError] = useState<string | null>(null)

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
  const shipping = subtotal > 0 ? 30000 : 0
  const total = subtotal + shipping

  useEffect(() => {
    if (!isCartLoading && (!cart?.items || cart.items.length === 0) && currentStep < 4) {
      navigate("/cart")
    }
  }, [cart, isCartLoading, currentStep, navigate])

  // --- STEP 1: REVIEW CART ---
  const Step1Review = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Review Your Cart</h2>
      <div className="border rounded-lg divide-y">
        {cart?.items.map((item) => (
          <div key={item.id} className="flex justify-between p-4">
            <div>
              <p className="font-medium">{item.product?.name || `Product ${item.product_id}`}</p>
              <p className="text-sm text-muted-foreground">Qty: {item.quantity}</p>
            </div>
            <p className="font-medium">{formatPrice((parseFloat(item.product?.price || "0")) * item.quantity)}</p>
          </div>
        ))}
      </div>
      <div className="flex justify-end gap-4">
        <Button variant="outline" onClick={() => navigate("/cart")}>Edit Cart</Button>
        <Button onClick={nextStep}>Continue to Shipping</Button>
      </div>
    </div>
  )

  // --- STEP 2: SHIPPING ---
  const Step2Shipping = () => {
    const form = useForm<z.infer<typeof shippingSchema>>({
      resolver: zodResolver(shippingSchema),
      defaultValues: shippingAddress || {
        fullName: "",
        phone: "",
        addressLine: "",
        city: "",
        country: "Vietnam",
      },
    })

    const onSubmit = (values: z.infer<typeof shippingSchema>) => {
      setShippingAddress(values)
      nextStep()
    }

    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold">Shipping Information</h2>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField control={form.control} name="fullName" render={({ field }) => (
              <FormItem><FormLabel>Full Name</FormLabel><FormControl><Input {...field} /></FormControl><FormMessage /></FormItem>
            )} />
            <FormField control={form.control} name="phone" render={({ field }) => (
              <FormItem><FormLabel>Phone Number</FormLabel><FormControl><Input {...field} /></FormControl><FormMessage /></FormItem>
            )} />
            <FormField control={form.control} name="addressLine" render={({ field }) => (
              <FormItem><FormLabel>Address Line</FormLabel><FormControl><Input {...field} /></FormControl><FormMessage /></FormItem>
            )} />
            <div className="grid grid-cols-2 gap-4">
              <FormField control={form.control} name="city" render={({ field }) => (
                <FormItem><FormLabel>City</FormLabel><FormControl><Input {...field} /></FormControl><FormMessage /></FormItem>
              )} />
              <FormField control={form.control} name="country" render={({ field }) => (
                <FormItem><FormLabel>Country</FormLabel><FormControl><Input {...field} /></FormControl><FormMessage /></FormItem>
              )} />
            </div>
            <div className="flex justify-between pt-4">
              <Button type="button" variant="outline" onClick={prevStep}>Back</Button>
              <Button type="submit">Continue to Payment</Button>
            </div>
          </form>
        </Form>
      </div>
    )
  }

  // --- STEP 3: PAYMENT & CONFIRM ---
  const Step3Payment = () => {
    const handlePlaceOrder = async () => {
      setCheckoutError(null)
      try {
        // 1. Create Order
        const orderResponse = await createOrder()
        const newOrderId = orderResponse.id
        setOrderId(newOrderId)

        // 2. Process Payment
        await processPayment({
          order_id: newOrderId,
          amount: total.toFixed(2),
          payment_method: paymentMethod
        })

        // 3. Move to Success Step
        nextStep()
        navigate("/checkout/success", { replace: true })
        
      } catch (error: any) {
        console.error("Checkout failed:", error)
        setCheckoutError(error?.response?.data?.detail || "Checkout failed. Please try again.")
      }
    }

    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold">Payment Method</h2>
        
        {checkoutError && (
          <div className="p-4 bg-destructive/10 text-destructive rounded-md font-medium">
            {checkoutError}
          </div>
        )}

        <div className="space-y-3">
          {["CREDIT_CARD", "PAYPAL", "COD"].map((method) => (
            <label key={method} className={`flex items-center p-4 border rounded-lg cursor-pointer transition-colors ${paymentMethod === method ? 'border-primary bg-primary/5' : 'hover:bg-muted'}`}>
              <input 
                type="radio" 
                name="paymentMethod" 
                value={method}
                checked={paymentMethod === method}
                onChange={(e) => setPaymentMethod(e.target.value)}
                className="mr-3 h-4 w-4 text-primary"
              />
              <span className="font-medium">
                {method === "COD" ? "Cash on Delivery (COD)" : method === "CREDIT_CARD" ? "Credit/Debit Card" : "PayPal"}
              </span>
            </label>
          ))}
        </div>

        <div className="bg-muted p-4 rounded-lg mt-6">
          <h3 className="font-semibold mb-2">Order Summary</h3>
          <div className="flex justify-between text-sm mb-1"><span className="text-muted-foreground">Subtotal</span><span>{formatPrice(subtotal)}</span></div>
          <div className="flex justify-between text-sm mb-1"><span className="text-muted-foreground">Shipping</span><span>{formatPrice(shipping)}</span></div>
          <div className="flex justify-between font-bold text-lg mt-3 pt-3 border-t"><span>Total</span><span>{formatPrice(total)}</span></div>
        </div>

        <div className="flex justify-between pt-4">
          <Button type="button" variant="outline" onClick={prevStep} disabled={isCreatingOrder || isProcessingPayment}>Back</Button>
          <Button onClick={handlePlaceOrder} disabled={isCreatingOrder || isProcessingPayment}>
            {isCreatingOrder || isProcessingPayment ? "Processing..." : "Place Order"}
          </Button>
        </div>
      </div>
    )
  }

  const steps = [
    { num: 1, title: "Cart" },
    { num: 2, title: "Shipping" },
    { num: 3, title: "Payment" }
  ]

  return (
    <div className="container py-12 max-w-4xl">
      {/* Stepper Header */}
      <div className="flex items-center justify-between mb-12 relative">
        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-0.5 bg-muted -z-10"></div>
        {steps.map((step) => {
          const isActive = currentStep === step.num
          const isPast = currentStep > step.num
          return (
            <div key={step.num} className="flex flex-col items-center bg-background px-4">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm border-2 transition-colors ${
                isActive ? "border-primary bg-primary text-primary-foreground" :
                isPast ? "border-primary bg-primary text-primary-foreground" :
                "border-muted text-muted-foreground bg-background"
              }`}>
                {isPast ? <Check className="h-5 w-5" /> : step.num}
              </div>
              <span className={`mt-2 text-sm font-medium ${isActive || isPast ? "text-foreground" : "text-muted-foreground"}`}>
                {step.title}
              </span>
            </div>
          )
        })}
      </div>

      {/* Step Content */}
      <Card>
        <CardContent className="p-6 md:p-8">
          {currentStep === 1 && <Step1Review />}
          {currentStep === 2 && <Step2Shipping />}
          {currentStep === 3 && <Step3Payment />}
        </CardContent>
      </Card>
    </div>
  )
}
