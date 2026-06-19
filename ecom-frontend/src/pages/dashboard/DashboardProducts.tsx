import { useState } from 'react'
import { formatPrice, getProductImageUrl } from '@/lib/utils'
import { apiClient } from '@/lib/axios'
import {
  useAdminProducts, useAdminCategories,
  useCreateProduct, useUpdateProduct, useDeleteProduct,
  AdminProduct, ProductPayload,
} from '@/hooks/useAdmin'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { Search, RefreshCw, Package, Plus, Pencil, Trash2, X } from 'lucide-react'

// ── Simple inline modal ────────────────────────────────────────
function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="relative z-10 w-full max-w-lg mx-4 bg-background border rounded-xl shadow-2xl animate-in fade-in-0 zoom-in-95 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-5 border-b sticky top-0 bg-background">
          <h2 className="font-semibold text-lg">{title}</h2>
          <button onClick={onClose} className="p-1.5 rounded-md hover:bg-muted transition-colors">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  )
}

// ── Confirm delete dialog ──────────────────────────────────────
function ConfirmDeleteDialog({ productName, onConfirm, onCancel, isLoading }: {
  productName: string; onConfirm: () => void; onCancel: () => void; isLoading: boolean
}) {
  return (
    <Modal title="Confirm Delete" onClose={onCancel}>
      <div className="space-y-4">
        <p className="text-sm text-muted-foreground">
          Are you sure you want to delete <span className="font-semibold text-foreground">"{productName}"</span>?
          This action cannot be undone and will permanently delete the product.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="outline" size="sm" onClick={onCancel}>Cancel</Button>
          <Button variant="destructive" size="sm" onClick={onConfirm} disabled={isLoading}>
            {isLoading ? 'Deleting…' : 'Delete'}
          </Button>
        </div>
      </div>
    </Modal>
  )
}

// ── Product form (create / edit) ───────────────────────────────
function ProductForm({ initial, onClose }: { initial?: AdminProduct; onClose: () => void }) {
  const isEdit = !!initial
  const { data: categories = [], isLoading: catsLoading } = useAdminCategories()
  const createProduct = useCreateProduct()
  const updateProduct = useUpdateProduct()

  const [form, setForm] = useState<Omit<ProductPayload, 'sku'> & { sku?: string }>({
    name: initial?.name ?? '',
    description: initial?.description ?? '',
    price: initial?.price ?? '',
    quantity: initial?.quantity ?? 0,
    status: (initial?.status as ProductPayload['status']) ?? 'active',
    category: initial?.category?.id ?? '',
    currency: 'VND',
  })
  const [error, setError] = useState('')
  const [images, setImages] = useState<{ url: string; alt_text?: string; is_primary?: boolean }[]>(
    initial?.images ?? []
  )
  const [imageUrlInput, setImageUrlInput] = useState('')
  const [isUploading, setIsUploading] = useState(false)

  const set = <K extends keyof ProductPayload>(k: K, v: ProductPayload[K]) =>
    setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // Validate
    if (!form.name.trim()) { setError('Product name is required.'); return }
    if (!form.price || isNaN(parseFloat(form.price as string))) { setError('Valid price is required.'); return }
    if (!form.category) { setError('Please select a category.'); return }

    try {
      // Auto-generate SKU from name + timestamp if not editing
      const autoSku = initial?.sku ||
        `${form.name.trim().toUpperCase().replace(/\s+/g, '-').substring(0, 10)}-${Date.now().toString(36).toUpperCase()}`

      const payload: ProductPayload = {
        ...form,
        sku: autoSku,
        price: parseFloat(form.price as string).toFixed(2),
        quantity: Number(form.quantity),
        images: images.map((img, i) => ({
          url: img.url,
          alt_text: img.alt_text || '',
          is_primary: img.is_primary ?? (i === 0),
        })),
      }

      if (isEdit && initial) {
        await updateProduct.mutateAsync({ id: initial.id, payload })
      } else {
        await createProduct.mutateAsync(payload)
      }
      onClose()
    } catch (err: any) {
      // Show detailed API error
      const apiError = err?.response?.data
      if (typeof apiError === 'object') {
        const messages = Object.entries(apiError)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
          .join('\n')
        setError(messages)
      } else {
        setError(apiError?.detail || 'Something went wrong. Check all fields and try again.')
      }
    }
  }

  const isPending = createProduct.isPending || updateProduct.isPending

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">

      {/* Status */}
        <div className="space-y-1.5">
          <Label htmlFor="pf-status">Status *</Label>
          <select
            id="pf-status"
            value={form.status}
            onChange={e => set('status', e.target.value as ProductPayload['status'])}
            className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          >
            <option value="active">Active (Published)</option>
            <option value="draft">Draft</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>

        {/* Name */}
        <div className="col-span-2 space-y-1.5">
          <Label htmlFor="pf-name">Product Name *</Label>
          <Input
            id="pf-name"
            value={form.name}
            onChange={e => set('name', e.target.value)}
            placeholder="e.g. Wireless Headphones Pro"
          />
        </div>

        {/* Price */}
        <div className="space-y-1.5">
          <Label htmlFor="pf-price">Price (VND) *</Label>
          <Input
            id="pf-price"
            type="number"
            step="1"
            min="0"
            value={form.price}
            onChange={e => set('price', e.target.value)}
            placeholder="0"
          />
        </div>

        {/* Quantity */}
        <div className="space-y-1.5">
          <Label htmlFor="pf-qty">Stock Quantity *</Label>
          <Input
            id="pf-qty"
            type="number"
            min="0"
            value={form.quantity}
            onChange={e => set('quantity', parseInt(e.target.value) || 0)}
          />
        </div>

        {/* Category */}
        <div className="col-span-2 space-y-1.5">
          <Label htmlFor="pf-cat">Category *</Label>
          {catsLoading ? (
            <div className="flex items-center gap-2 h-9">
              <Skeleton className="h-9 w-full" />
              <span className="text-xs text-muted-foreground whitespace-nowrap">Loading…</span>
            </div>
          ) : categories.length === 0 ? (
            <div className="p-3 border rounded-md bg-yellow-50 dark:bg-yellow-900/10 border-yellow-200 dark:border-yellow-800">
              <p className="text-sm text-yellow-800 dark:text-yellow-400 font-medium">⚠️ No categories in database</p>
              <p className="text-xs text-muted-foreground mt-1">Run: <code className="bg-muted px-1 rounded">docker compose exec product-service python manage.py seed_categories</code></p>
            </div>
          ) : (
            <select
              id="pf-cat"
              value={form.category}
              onChange={e => set('category', e.target.value)}
              className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            >
              <option value="">— Select a category —</option>
              {categories.map(c => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Description */}
        <div className="col-span-2 space-y-1.5">
          <Label htmlFor="pf-desc">Description</Label>
          <textarea
            id="pf-desc"
            value={form.description}
            onChange={e => set('description', e.target.value)}
            rows={3}
            className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring resize-none"
            placeholder="Product description…"
          />
        </div>

        {/* Product Images */}
        <div className="col-span-2 space-y-2.5">
          <Label>Product Images</Label>
          
          {images.length > 0 && (
            <div className="grid grid-cols-4 gap-3 p-3 border rounded-md bg-muted/20">
              {images.map((img, idx) => (
                <div key={idx} className="relative aspect-square border rounded-md overflow-hidden bg-background group">
                  <img src={getProductImageUrl(img.url)} alt={img.alt_text || "Preview"} className="w-full h-full object-cover" />
                  
                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-between p-1">
                    <button
                      type="button"
                      onClick={() => {
                        setImages(prev => prev.filter((_, i) => i !== idx))
                      }}
                      className="self-end bg-destructive/90 text-destructive-foreground p-1 rounded hover:bg-destructive transition-colors"
                      title="Remove image"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                    
                    <button
                      type="button"
                      onClick={() => {
                        setImages(prev => prev.map((item, i) => ({
                          ...item,
                          is_primary: i === idx
                        })))
                      }}
                      className={`text-[10px] px-1.5 py-0.5 rounded text-center w-full font-medium ${
                        img.is_primary ? "bg-green-600 text-white" : "bg-black/60 text-white hover:bg-black/80"
                      } transition-colors`}
                    >
                      {img.is_primary ? "Primary" : "Set Primary"}
                    </button>
                  </div>
                  
                  {img.is_primary && (
                    <span className="absolute top-1 left-1 bg-green-600 text-white text-[9px] px-1.5 py-0.5 rounded font-semibold shadow-sm">
                      Primary
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}

          <div className="space-y-2 border rounded-md p-3 bg-muted/10">
            <div className="flex gap-2 items-center">
              <Input
                type="text"
                placeholder="Paste Image URL Link..."
                value={imageUrlInput}
                onChange={e => setImageUrlInput(e.target.value)}
                className="flex-1 text-xs h-8"
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  if (!imageUrlInput.trim()) return
                  setImages(prev => [
                    ...prev,
                    { url: imageUrlInput.trim(), is_primary: prev.length === 0 }
                  ])
                  setImageUrlInput('')
                }}
                className="h-8 text-xs shrink-0"
              >
                Link Image
              </Button>
            </div>

            <div className="flex gap-2 items-center justify-between border-t pt-2 mt-2">
              <span className="text-xs text-muted-foreground">Or upload image from computer:</span>
              <label className="relative shrink-0 cursor-pointer h-8 px-3 rounded-md border border-input bg-background flex items-center justify-center text-xs font-medium shadow-sm hover:bg-muted transition-colors">
                {isUploading ? "Uploading..." : "Select File"}
                <input
                  type="file"
                  accept="image/*"
                  onChange={async (e) => {
                    const file = e.target.files?.[0]
                    if (!file) return
                    
                    const formData = new FormData()
                    formData.append("image", file)
                    
                    try {
                      setIsUploading(true)
                      const { data } = await apiClient.post<{ url: string }>("/products/upload-image/", formData, {
                        headers: { "Content-Type": "multipart/form-data" }
                      })
                      setImages(prev => [
                        ...prev,
                        { url: data.url, alt_text: file.name, is_primary: prev.length === 0 }
                      ])
                    } catch (err: any) {
                      setError("Failed to upload image: " + (err.response?.data?.detail || err.message))
                    } finally {
                      setIsUploading(false)
                    }
                  }}
                  className="absolute inset-0 opacity-0 w-full cursor-pointer"
                  disabled={isUploading}
                />
              </label>
            </div>
          </div>
        </div>

      </div>

      {error && (
        <pre className="text-xs text-destructive bg-destructive/10 px-3 py-2 rounded-md whitespace-pre-wrap border border-destructive/20">
          {error}
        </pre>
      )}

      <div className="flex justify-end gap-2 pt-2 border-t">
        <Button type="button" variant="outline" size="sm" onClick={onClose}>Cancel</Button>
        <Button type="submit" size="sm" disabled={isPending}>
          {isPending ? 'Saving…' : isEdit ? 'Save Changes' : 'Create Product'}
        </Button>
      </div>
    </form>
  )
}

// ── Status badge helper ────────────────────────────────────────
const statusStyle: Record<string, string> = {
  active:   'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400',
  draft:    'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
  inactive: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400',
  deleted:  'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400',
}


// ── Main Page ──────────────────────────────────────────────────
export default function DashboardProducts() {
  const [search, setSearch] = useState('')
  const [modal, setModal] = useState<'create' | 'edit' | 'delete' | null>(null)
  const [selected, setSelected] = useState<AdminProduct | null>(null)

  const { data: products, isLoading, refetch } = useAdminProducts(search || undefined)
  const deleteProduct = useDeleteProduct()

  const openEdit = (p: AdminProduct) => { setSelected(p); setModal('edit') }
  const openDelete = (p: AdminProduct) => { setSelected(p); setModal('delete') }
  const closeModal = () => { setModal(null); setSelected(null) }

  const handleDelete = async () => {
    if (!selected) return
    await deleteProduct.mutateAsync(selected.id)
    closeModal()
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Products</h1>
          <p className="text-muted-foreground mt-1">Manage your product catalog</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" /> Refresh
          </Button>
          <Button size="sm" onClick={() => setModal('create')}>
            <Plus className="mr-2 h-4 w-4" /> Add Product
          </Button>
        </div>
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by name or SKU..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            {(products || []).length} Product{(products || []).length !== 1 ? 's' : ''}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map(i => <Skeleton key={i} className="h-14 w-full" />)}
            </div>
          ) : !products || products.length === 0 ? (
            <div className="text-center py-16">
              <Package className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground font-medium">No products found.</p>
              <Button size="sm" className="mt-4" onClick={() => setModal('create')}>
                <Plus className="mr-2 h-4 w-4" /> Add your first product
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-3 font-medium text-muted-foreground">Product</th>
                    <th className="text-left py-3 px-3 font-medium text-muted-foreground">Category</th>
                    <th className="text-left py-3 px-3 font-medium text-muted-foreground">Price</th>
                    <th className="text-left py-3 px-3 font-medium text-muted-foreground">Stock</th>
                    <th className="text-left py-3 px-3 font-medium text-muted-foreground">Status</th>
                    <th className="text-right py-3 px-3 font-medium text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {products.map((product) => (
                    <tr key={product.id} className="border-b last:border-0 hover:bg-muted/30 transition-colors">
                      <td className="py-3 px-3">
                        <p className="font-medium">{product.name}</p>
                        <p className="text-xs text-muted-foreground font-mono">SKU: {product.sku}</p>
                      </td>
                      <td className="py-3 px-3">
                        <Badge variant="outline" className="text-xs">
                          {product.category?.name || product.category_name || 'Uncategorized'}
                        </Badge>
                      </td>
                      <td className="py-3 px-3 font-semibold">
                        {formatPrice(product.price)}
                      </td>
                      <td className="py-3 px-3">
                        <span className={product.quantity === 0 ? "text-destructive font-semibold" : "font-medium"}>
                          {product.quantity}
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium capitalize ${statusStyle[product.status] || 'bg-muted text-muted-foreground'}`}>
                          {product.status}
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        <div className="flex justify-end gap-1">
                          <Button
                            size="sm" variant="ghost"
                            className="h-8 w-8 p-0 text-muted-foreground hover:text-foreground"
                            onClick={() => openEdit(product)}
                            title="Edit product"
                          >
                            <Pencil className="h-3.5 w-3.5" />
                          </Button>
                          <Button
                            size="sm" variant="ghost"
                            className="h-8 w-8 p-0 text-muted-foreground hover:text-destructive"
                            onClick={() => openDelete(product)}
                            title="Delete product"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modals */}
      {modal === 'create' && (
        <Modal title="Add New Product" onClose={closeModal}>
          <ProductForm onClose={closeModal} />
        </Modal>
      )}
      {modal === 'edit' && selected && (
        <Modal title={`Edit: ${selected.name}`} onClose={closeModal}>
          <ProductForm initial={selected} onClose={closeModal} />
        </Modal>
      )}
      {modal === 'delete' && selected && (
        <ConfirmDeleteDialog
          productName={selected.name}
          onConfirm={handleDelete}
          onCancel={closeModal}
          isLoading={deleteProduct.isPending}
        />
      )}
    </div>
  )
}
