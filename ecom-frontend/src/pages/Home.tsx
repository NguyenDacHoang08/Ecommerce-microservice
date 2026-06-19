import { ArrowRight, Laptop, Shirt, BookOpen } from 'lucide-react'
import { Link } from 'react-router-dom'

const Home = () => {
  return (
    <div className="flex flex-col gap-12 pb-12">
      {/* Hero Section */}
      <section className="bg-muted/30 py-20">
        <div className="container flex flex-col items-center text-center gap-6">
          <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight max-w-3xl">
            Discover the future of <span className="text-primary">E-Commerce</span>
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl">
            Shop the latest trends in fashion, electronics, and books with our modern microservices architecture.
          </p>
          <div className="flex gap-4 mt-4">
            <Link to="/products" className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-11 px-8">
              Shop Now <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="container">
        <h2 className="text-3xl font-bold mb-8 text-center">Shop by Category</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Link to="/products?category=electronics" className="group block overflow-hidden rounded-lg border bg-card text-card-foreground shadow-sm transition-all hover:shadow-md">
            <div className="p-8 flex flex-col items-center text-center gap-4">
              <div className="p-4 bg-primary/10 rounded-full text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                <Laptop className="h-8 w-8" />
              </div>
              <h3 className="text-xl font-bold">Electronics</h3>
              <p className="text-muted-foreground text-sm">Smartphones, Laptops & Accessories</p>
            </div>
          </Link>
          
          <Link to="/products?category=fashion" className="group block overflow-hidden rounded-lg border bg-card text-card-foreground shadow-sm transition-all hover:shadow-md">
            <div className="p-8 flex flex-col items-center text-center gap-4">
              <div className="p-4 bg-primary/10 rounded-full text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                <Shirt className="h-8 w-8" />
              </div>
              <h3 className="text-xl font-bold">Fashion</h3>
              <p className="text-muted-foreground text-sm">Clothing, Shoes & Accessories</p>
            </div>
          </Link>

          <Link to="/products?category=books" className="group block overflow-hidden rounded-lg border bg-card text-card-foreground shadow-sm transition-all hover:shadow-md">
            <div className="p-8 flex flex-col items-center text-center gap-4">
              <div className="p-4 bg-primary/10 rounded-full text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                <BookOpen className="h-8 w-8" />
              </div>
              <h3 className="text-xl font-bold">Books</h3>
              <p className="text-muted-foreground text-sm">Fiction, Non-fiction & Textbooks</p>
            </div>
          </Link>
        </div>
      </section>
    </div>
  )
}

export default Home
