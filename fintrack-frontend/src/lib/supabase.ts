import { createClient } from '@supabase/supabase-js'
// Temporary Database type until we fix the generated types
type Database = {
  public: {
    Tables: {
      transactions: {
        Row: {
          id: string
          user_id: string
          amount: number
          description: string
          date: string
          merchant: string | null
          category: string | null
          subcategory: string | null
          transaction_type: string
          status: string
          payment_method: string | null
          account_type: string | null
          confidence: number | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          amount: number
          description: string
          date: string
          merchant?: string | null
          category?: string | null
          subcategory?: string | null
          transaction_type: string
          status?: string
          payment_method?: string | null
          account_type?: string | null
          confidence?: number | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          amount?: number
          description?: string
          date?: string
          merchant?: string | null
          category?: string | null
          subcategory?: string | null
          transaction_type?: string
          status?: string
          payment_method?: string | null
          account_type?: string | null
          confidence?: number | null
          created_at?: string
          updated_at?: string
        }
      }
      profiles: {
        Row: {
          id: string
          username: string
          email: string
          full_name: string | null
          created_at: string
        }
        Insert: {
          id?: string
          username: string
          email: string
          full_name?: string | null
          created_at?: string
        }
        Update: {
          id?: string
          username?: string
          email?: string
          full_name?: string | null
          created_at?: string
        }
      }
    }
  }
}

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true
  }
})

// Type aliases for easier use
export type Transaction = Database['public']['Tables']['transactions']['Row']
export type TransactionInsert = Database['public']['Tables']['transactions']['Insert']
export type TransactionUpdate = Database['public']['Tables']['transactions']['Update']
export type Profile = Database['public']['Tables']['profiles']['Row']
export type ProfileInsert = Database['public']['Tables']['profiles']['Insert']
export type ProfileUpdate = Database['public']['Tables']['profiles']['Update']
