export interface Product {
  id: string;
  name: string;
  slug: string;
  description: string;
  price: string;
  quantity: number;
  status: string;
  category: string;
  polymorphic_ctype: number;
  created_at: string;
  updated_at: string;
  // Specific fields
  author?: string;
  isbn?: string;
  brand?: string;
  model_name?: string;
  warranty_months?: number;
  size?: string;
  color?: string;
  images?: { id: string; url: string; alt_text?: string; is_primary: boolean; order: number }[];
  image_url?: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface CartItem {
  id: number;
  product_id: string;
  quantity: number;
  product?: Product; // We might fetch this separately or the backend might serialize it
}

export interface Cart {
  id: string;
  user_id: string;
  items: CartItem[];
  created_at: string;
  updated_at: string;
}
