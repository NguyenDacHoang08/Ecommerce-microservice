const Footer = () => {
  return (
    <footer className="border-t bg-muted/40 py-12">
      <div className="container grid grid-cols-1 md:grid-cols-4 gap-8">
        <div>
          <h3 className="text-lg font-bold mb-4">MicroEcom</h3>
          <p className="text-sm text-muted-foreground">
            A modern microservices e-commerce platform built with React, Vite, and Tailwind CSS.
          </p>
        </div>
        <div>
          <h4 className="font-semibold mb-4">Shop</h4>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li><a href="#" className="hover:text-foreground">All Products</a></li>
            <li><a href="#" className="hover:text-foreground">Electronics</a></li>
            <li><a href="#" className="hover:text-foreground">Fashion</a></li>
            <li><a href="#" className="hover:text-foreground">Books</a></li>
          </ul>
        </div>
        <div>
          <h4 className="font-semibold mb-4">Support</h4>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li><a href="#" className="hover:text-foreground">FAQ</a></li>
            <li><a href="#" className="hover:text-foreground">Shipping</a></li>
            <li><a href="#" className="hover:text-foreground">Returns</a></li>
            <li><a href="#" className="hover:text-foreground">Contact Us</a></li>
          </ul>
        </div>
        <div>
          <h4 className="font-semibold mb-4">Newsletter</h4>
          <p className="text-sm text-muted-foreground mb-4">Subscribe for the latest updates and offers.</p>
          <div className="flex gap-2">
            <input type="email" placeholder="Enter your email" className="h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm" />
            <button className="h-9 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90">
              Subscribe
            </button>
          </div>
        </div>
      </div>
      <div className="container mt-12 pt-8 border-t text-center text-sm text-muted-foreground">
        <p>&copy; {new Date().getFullYear()} MicroEcom. All rights reserved.</p>
      </div>
    </footer>
  )
}

export default Footer
