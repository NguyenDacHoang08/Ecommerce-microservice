import { useState } from "react"
import { useSearchParams } from "react-router-dom"
import { useProducts } from "@/hooks/useProducts"
import { ProductCard } from "@/components/product/ProductCard"
import { Skeleton } from "@/components/ui/skeleton"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Search } from "lucide-react"

export default function ProductList() {
  const [searchParams, setSearchParams] = useSearchParams()
  const page = parseInt(searchParams.get("page") || "1", 10)
  const category = searchParams.get("category") || ""
  const initialSearch = searchParams.get("search") || ""
  
  const [searchInput, setSearchInput] = useState(initialSearch)

  const { data, isLoading, isError } = useProducts({ page, search: initialSearch, category })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setSearchParams(prev => {
      if (searchInput) prev.set("search", searchInput)
      else prev.delete("search")
      prev.set("page", "1")
      return prev
    })
  }

  const handleCategoryChange = (newCategory: string) => {
    setSearchParams(prev => {
      if (newCategory) prev.set("category", newCategory)
      else prev.delete("category")
      prev.set("page", "1")
      return prev
    })
  }

  const handlePageChange = (newPage: number) => {
    setSearchParams(prev => {
      prev.set("page", newPage.toString())
      return prev
    })
  }

  const categories = ["", "electronics", "fashion", "books"]

  return (
    <div className="container py-8 flex flex-col gap-8 md:flex-row">
      {/* Sidebar Filters */}
      <div className="w-full md:w-64 space-y-6 flex-shrink-0">
        <div>
          <h3 className="font-semibold mb-3">Categories</h3>
          <div className="space-y-2 flex flex-col">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => handleCategoryChange(cat)}
                className={`text-left px-3 py-2 rounded-md text-sm transition-colors ${
                  category === cat ? "bg-primary text-primary-foreground font-medium" : "hover:bg-muted"
                }`}
              >
                {cat === "" ? "All Categories" : cat.charAt(0).toUpperCase() + cat.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 space-y-6">
        {/* Search Bar */}
        <form onSubmit={handleSearch} className="flex gap-2">
          <Input 
            placeholder="Search products..." 
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="max-w-md"
          />
          <Button type="submit" variant="secondary">
            <Search className="h-4 w-4 mr-2" />
            Search
          </Button>
        </form>

        {/* Results */}
        {isError && (
          <div className="p-8 text-center bg-destructive/10 text-destructive rounded-lg border border-destructive/20">
            Failed to load products. Please try again later.
          </div>
        )}

        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="flex flex-col space-y-3">
                <Skeleton className="h-[250px] w-full rounded-xl" />
                <div className="space-y-2">
                  <Skeleton className="h-4 w-[250px]" />
                  <Skeleton className="h-4 w-[200px]" />
                </div>
              </div>
            ))}
          </div>
        ) : data?.results?.length === 0 ? (
          <div className="p-12 text-center border rounded-lg bg-muted/20">
            <h3 className="text-xl font-bold">No products found</h3>
            <p className="text-muted-foreground mt-2">Try adjusting your search or filters.</p>
            {(initialSearch || category) && (
              <Button 
                variant="outline" 
                className="mt-4"
                onClick={() => setSearchParams({})}
              >
                Clear all filters
              </Button>
            )}
          </div>
        ) : (
          <>
            <div className="text-sm text-muted-foreground">
              Found <span className="font-semibold text-foreground">{data?.count}</span> products
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {data?.results.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>

            {/* Pagination */}
            {data && data.count > 0 && (
              <div className="flex items-center justify-center gap-2 mt-8">
                <Button 
                  variant="outline" 
                  disabled={!data.previous}
                  onClick={() => handlePageChange(page - 1)}
                >
                  Previous
                </Button>
                <span className="text-sm text-muted-foreground">
                  Page {page} of {Math.ceil(data.count / 20)}
                </span>
                <Button 
                  variant="outline" 
                  disabled={!data.next}
                  onClick={() => handlePageChange(page + 1)}
                >
                  Next
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
