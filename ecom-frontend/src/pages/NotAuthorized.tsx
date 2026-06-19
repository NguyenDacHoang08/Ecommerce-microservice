import { useNavigate } from 'react-router-dom'
import { ShieldX, ArrowLeft, Home } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function NotAuthorized() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/20 px-4">
      <div className="text-center max-w-md">
        {/* Icon */}
        <div className="mx-auto mb-6 h-24 w-24 rounded-full bg-destructive/10 flex items-center justify-center">
          <ShieldX className="h-12 w-12 text-destructive" />
        </div>

        {/* Code */}
        <p className="text-8xl font-black text-muted-foreground/20 select-none leading-none mb-4">403</p>

        {/* Title */}
        <h1 className="text-2xl font-bold tracking-tight mb-2">Access Denied</h1>
        <p className="text-muted-foreground mb-8">
          You don't have permission to access this page. Please contact your administrator if you believe this is a mistake.
        </p>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Button variant="outline" onClick={() => navigate(-1)}>
            <ArrowLeft className="mr-2 h-4 w-4" /> Go Back
          </Button>
          <Button onClick={() => navigate('/')}>
            <Home className="mr-2 h-4 w-4" /> Go to Home
          </Button>
        </div>
      </div>
    </div>
  )
}
