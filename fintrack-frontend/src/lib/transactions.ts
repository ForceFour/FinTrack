import { supabase, type Transaction, type TransactionUpdate } from './supabase'

export interface TransactionFilters {
  category?: string
  start_date?: string
  end_date?: string
  min_amount?: number
  max_amount?: number
  transaction_type?: string
  status?: string
}

export interface TransactionResponse {
  data: Transaction[]
  count: number
  error: string | null
}

// Create a new transaction
export async function createTransaction(transaction: {
  user_id: string
  amount: number
  description: string
  date: string
  transaction_type: 'DEBIT' | 'CREDIT'
  status?: 'PENDING' | 'COMPLETED' | 'FAILED'
  category?: string | null
  merchant?: string | null
  confidence_score?: number | null
}): Promise<{ data: Transaction | null, error: string | null }> {
  try {
    const { data, error } = await supabase
      .from('transactions')
      .insert({
        user_id: transaction.user_id,
        amount: transaction.amount,
        description: transaction.description,
        date: transaction.date,
        transaction_type: transaction.transaction_type === 'DEBIT' ? 'debit' : 'credit',
        status: (transaction.status || 'PENDING').toLowerCase(),
        category: transaction.category,
        merchant: transaction.merchant,
        confidence: transaction.confidence_score,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })
      .select()
      .single()

    if (error) {
      return { data: null, error: error.message }
    }

    return { data, error: null }
  } catch {
    return { data: null, error: 'An unexpected error occurred' }
  }
}

// Get a single transaction by ID
export async function getTransaction(id: string, userId: string): Promise<{ data: Transaction | null, error: string | null }> {
  try {
    const { data, error } = await supabase
      .from('transactions')
      .select('*')
      .eq('id', id)
      .eq('user_id', userId)
      .single()

    if (error) {
      return { data: null, error: error.message }
    }

    return { data, error: null }
  } catch {
    return { data: null, error: 'An unexpected error occurred' }
  }
}

// Get transactions with filters and pagination
export async function getTransactions(
  userId: string,
  filters: TransactionFilters = {},
  page: number = 1,
  limit: number = 50
): Promise<TransactionResponse> {
  try {
    let query = supabase
      .from('transactions')
      .select('*', { count: 'exact' })
      .eq('user_id', userId)
      .order('date', { ascending: false })
      .range((page - 1) * limit, page * limit - 1)

    // Apply filters
    if (filters.category) {
      query = query.eq('category', filters.category)
    }

    if (filters.start_date) {
      query = query.gte('date', filters.start_date)
    }

    if (filters.end_date) {
      query = query.lte('date', filters.end_date)
    }

    if (filters.min_amount !== undefined) {
      query = query.gte('amount', filters.min_amount)
    }

    if (filters.max_amount !== undefined) {
      query = query.lte('amount', filters.max_amount)
    }

    if (filters.transaction_type) {
      query = query.eq('transaction_type', filters.transaction_type as 'DEBIT' | 'CREDIT')
    }

    if (filters.status) {
      query = query.eq('status', filters.status as 'PENDING' | 'COMPLETED' | 'FAILED')
    }

    const { data, error, count } = await query

    if (error) {
      return { data: [], count: 0, error: error.message }
    }

    return { data: data || [], count: count || 0, error: null }
  } catch {
    return { data: [], count: 0, error: 'An unexpected error occurred' }
  }
}

// Update a transaction
export async function updateTransaction(
  id: string,
  userId: string,
  updates: Partial<Omit<TransactionUpdate, 'id' | 'user_id' | 'created_at'>>
): Promise<{ data: Transaction | null, error: string | null }> {
  try {
    const { data, error } = await supabase
      .from('transactions')
      .update({ ...updates, updated_at: new Date().toISOString() })
      .eq('id', id)
      .eq('user_id', userId)
      .select()
      .single()

    if (error) {
      return { data: null, error: error.message }
    }

    return { data, error: null }
  } catch {
    return { data: null, error: 'An unexpected error occurred' }
  }
}

// Delete a transaction
export async function deleteTransaction(id: string, userId: string): Promise<{ error: string | null }> {
  try {
    const { error } = await supabase
      .from('transactions')
      .delete()
      .eq('id', id)
      .eq('user_id', userId)

    if (error) {
      return { error: error.message }
    }

    return { error: null }
  } catch {
    return { error: 'An unexpected error occurred' }
  }
}

// Get transaction statistics
export async function getTransactionStats(userId: string, startDate?: string, endDate?: string): Promise<{
  data: {
    total_transactions: number
    total_amount: number
    average_amount: number
    categories: { category: string, count: number, total: number }[]
  } | null,
  error: string | null
}> {
  try {
    let query = supabase
      .from('transactions')
      .select('amount, category, transaction_type')
      .eq('user_id', userId)

    if (startDate) {
      query = query.gte('date', startDate)
    }

    if (endDate) {
      query = query.lte('date', endDate)
    }

    const { data, error } = await query

    if (error) {
      return { data: null, error: error.message }
    }

    if (!data) {
      return {
        data: {
          total_transactions: 0,
          total_amount: 0,
          average_amount: 0,
          categories: []
        },
        error: null
      }
    }

    const totalTransactions = data.length
    const totalAmount = data.reduce((sum, t) => sum + Math.abs(t.amount), 0)
    const averageAmount = totalTransactions > 0 ? totalAmount / totalTransactions : 0

    // Group by category
    const categoryMap = new Map<string, { count: number, total: number }>()
    data.forEach(t => {
      const category = t.category || 'Uncategorized'
      const existing = categoryMap.get(category) || { count: 0, total: 0 }
      categoryMap.set(category, {
        count: existing.count + 1,
        total: existing.total + Math.abs(t.amount)
      })
    })

    const categories = Array.from(categoryMap.entries()).map(([category, stats]) => ({
      category,
      count: stats.count,
      total: stats.total
    }))

    return {
      data: {
        total_transactions: totalTransactions,
        total_amount: totalAmount,
        average_amount: averageAmount,
        categories
      },
      error: null
    }
  } catch {
    return { data: null, error: 'An unexpected error occurred' }
  }
}
