import { useState } from 'react'
import { ShoppingCart, User, Search, Menu, X, ChevronDown, LogOut, Settings, PackageOpen, LayoutDashboard, Sparkles } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/useAuthStore'
import { useCart } from '@/hooks/useCart'
import { ModeToggle } from '@/components/theme-toggle'

const Header = () => {
  const navigate = useNavigate()
  const { isAuthenticated, logout, user } = useAuthStore()
  const { data: cart } = useCart()
  
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [isCategoryOpen, setIsCategoryOpen] = useState(false)
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")

  const cartItemCount = cart?.items?.reduce((total, item) => total + item.quantity, 0) || 0

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`/products?search=${encodeURIComponent(searchQuery)}`)
      setIsMobileMenuOpen(false)
    }
  }

  const handleLogout = async () => {
    setIsUserMenuOpen(false)
    await logout()
    navigate('/login')
  }

  const isAdminOrStaff = user?.role === 'admin' || user?.role === 'staff'

  const categories = [
    { name: "Electronics", path: "/products?category=electronics" },
    { name: "Fashion", path: "/products?category=fashion" },
    { name: "Books", path: "/products?category=books" },
  ]

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        
        {/* Mobile Menu Toggle & Logo */}
        <div className="flex items-center gap-4">
          <button 
            className="md:hidden p-2 -ml-2"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          >
            {isMobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
          <Link to="/" className="flex items-center space-x-2">
            <span className="font-bold text-xl tracking-tight text-primary">MicroEcom</span>
          </Link>
        </div>

        {/* Desktop Nav */}
        <nav className="hidden md:flex items-center gap-6 text-sm font-medium">
          <Link to="/products" className="transition-colors hover:text-foreground/80">Shop</Link>
          <Link
            to="/recommendations"
            className="flex items-center gap-1.5 transition-colors hover:text-primary font-medium text-primary/80 relative group"
          >
            <Sparkles className="h-3.5 w-3.5 text-primary" />
            Gợi ý
            <span className="absolute -top-1 -right-2 flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
            </span>
          </Link>
          
          {/* Custom Dropdown for Categories */}
          <div className="relative">
            <button 
              className="flex items-center gap-1 transition-colors hover:text-foreground/80"
              onClick={() => setIsCategoryOpen(!isCategoryOpen)}
              onBlur={() => setTimeout(() => setIsCategoryOpen(false), 200)}
            >
              Categories <ChevronDown className="h-4 w-4" />
            </button>
            
            {isCategoryOpen && (
              <div className="absolute top-full left-0 mt-2 w-48 rounded-md border bg-popover text-popover-foreground shadow-md outline-none animate-in fade-in-0 zoom-in-95">
                <div className="py-1">
                  {categories.map((cat) => (
                    <Link 
                      key={cat.name}
                      to={cat.path} 
                      className="block px-4 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
                    >
                      {cat.name}
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </div>
        </nav>

        {/* Search & Actions */}
        <div className="flex items-center gap-2 md:gap-4">
          <form onSubmit={handleSearch} className="hidden lg:block relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              type="search"
              placeholder="Search products..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-9 w-64 rounded-md border border-input bg-transparent px-8 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            />
          </form>
          
          <ModeToggle />

          <Link to="/cart" className="relative p-2 rounded-md hover:bg-accent hover:text-accent-foreground">
            <ShoppingCart className="h-5 w-5" />
            {cartItemCount > 0 && (
              <span className="absolute top-0 right-0 h-4 w-4 rounded-full bg-primary text-[10px] font-bold text-primary-foreground flex items-center justify-center">
                {cartItemCount}
              </span>
            )}
          </Link>
          
          {isAuthenticated ? (
            <div className="relative">
              <button 
                className="p-2 rounded-full bg-muted border hover:bg-accent"
                onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                onBlur={() => setTimeout(() => setIsUserMenuOpen(false), 200)}
              >
                <User className="h-4 w-4" />
              </button>
              
              {isUserMenuOpen && (
                <div className="absolute top-full right-0 mt-2 w-56 rounded-md border bg-popover text-popover-foreground shadow-md outline-none animate-in fade-in-0 zoom-in-95">
                  <div className="p-3 border-b">
                    <p className="text-sm font-medium">{user?.full_name || user?.email || 'My Account'}</p>
                    {user?.role && (
                      <p className="text-xs text-muted-foreground capitalize mt-0.5">{user.role}</p>
                    )}
                  </div>
                  <div className="py-1">
                    {isAdminOrStaff && (
                      <Link to="/dashboard" className="flex items-center px-4 py-2 text-sm hover:bg-accent hover:text-accent-foreground text-primary font-medium">
                        <LayoutDashboard className="mr-2 h-4 w-4" /> Dashboard
                      </Link>
                    )}
                    <Link to="/profile" className="flex items-center px-4 py-2 text-sm hover:bg-accent hover:text-accent-foreground">
                      <Settings className="mr-2 h-4 w-4" /> Profile
                    </Link>
                    <Link to="/profile?tab=orders" className="flex items-center px-4 py-2 text-sm hover:bg-accent hover:text-accent-foreground">
                      <PackageOpen className="mr-2 h-4 w-4" /> Order History
                    </Link>
                  </div>
                  <div className="border-t py-1">
                    <button 
                      onClick={handleLogout}
                      className="flex w-full items-center px-4 py-2 text-sm text-destructive hover:bg-accent"
                    >
                      <LogOut className="mr-2 h-4 w-4" /> Log out
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <Link to="/login" className="p-2 text-sm font-medium hover:text-primary">
              Log in
            </Link>
          )}
        </div>
      </div>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="md:hidden border-t bg-background p-4 animate-in slide-in-from-top-2">
          <form onSubmit={handleSearch} className="relative mb-4">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              type="search"
              placeholder="Search products..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full h-9 rounded-md border border-input bg-transparent px-8 py-1 text-sm"
            />
          </form>
          
          <nav className="flex flex-col space-y-3">
            <Link to="/products" className="font-medium" onClick={() => setIsMobileMenuOpen(false)}>Shop All</Link>
            <Link
              to="/recommendations"
              className="flex items-center gap-2 font-medium text-primary"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              <Sparkles className="h-4 w-4" />
              Sản phẩm gợi ý
            </Link>
            <div className="font-medium text-muted-foreground mt-2">Categories</div>
            <div className="flex flex-col pl-4 border-l space-y-2">
              {categories.map((cat) => (
                <Link 
                  key={cat.name} 
                  to={cat.path} 
                  className="text-sm"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  {cat.name}
                </Link>
              ))}
            </div>
          </nav>
        </div>
      )}
    </header>
  )
}

export default Header
