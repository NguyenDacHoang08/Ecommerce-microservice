import { create } from 'zustand'

interface ShippingAddress {
  fullName: string
  phone: string
  addressLine: string
  city: string
  country: string
}

interface CheckoutState {
  currentStep: number
  shippingAddress: ShippingAddress | null
  paymentMethod: string
  orderId: string | null
  
  setStep: (step: number) => void
  nextStep: () => void
  prevStep: () => void
  setShippingAddress: (address: ShippingAddress) => void
  setPaymentMethod: (method: string) => void
  setOrderId: (id: string) => void
  resetCheckout: () => void
}

export const useCheckoutStore = create<CheckoutState>((set) => ({
  currentStep: 1,
  shippingAddress: null,
  paymentMethod: "CREDIT_CARD",
  orderId: null,

  setStep: (step) => set({ currentStep: step }),
  nextStep: () => set((state) => ({ currentStep: Math.min(state.currentStep + 1, 4) })),
  prevStep: () => set((state) => ({ currentStep: Math.max(state.currentStep - 1, 1) })),
  
  setShippingAddress: (address) => set({ shippingAddress: address }),
  setPaymentMethod: (method) => set({ paymentMethod: method }),
  setOrderId: (id) => set({ orderId: id }),
  
  resetCheckout: () => set({ 
    currentStep: 1, 
    shippingAddress: null, 
    paymentMethod: "CREDIT_CARD", 
    orderId: null 
  }),
}))
