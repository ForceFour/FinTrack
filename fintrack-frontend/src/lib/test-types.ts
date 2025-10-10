// Type checking test for database types
import type { Transaction, TransactionInsert, Profile, ProfileInsert } from '../lib/supabase'

// Test 1: Transaction type should have all required properties
const testTransaction: Transaction = {
  id: '123',
  user_id: 'user123',
  amount: 100.50,
  description: 'Test transaction',
  date: '2024-01-01',
  merchant: 'Test Store',
  category: 'Food',
  subcategory: 'Groceries',
  transaction_type: 'DEBIT',
  status: 'COMPLETED',
  account_id: null,
  bank_transaction_id: null,
  confidence_score: 0.95,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  is_recurring: false,
  location: null,
  notes: null,
  processed_by_agent: null,
  processing_version: null,
  recurring_pattern: null,
  tags: null
}

// Test 2: TransactionInsert should allow optional fields
const testTransactionInsert: TransactionInsert = {
  user_id: 'user123',
  amount: 50.00,
  description: 'Insert test',
  date: '2024-01-01',
  transaction_type: 'CREDIT',
  created_at: '2024-01-01T00:00:00Z',
  id: 'insert123',
  status: 'PENDING',
  updated_at: '2024-01-01T00:00:00Z'
  // Many fields are optional
}

// Test 3: Profile type should match database schema
const testProfile: Profile = {
  id: 'user123',
  username: 'testuser',
  email: 'test@example.com',
  full_name: 'Test User',
  hashed_password: 'hashed123',
  is_active: true,
  is_verified: true,
  preferences: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  last_login: null
}

// Test 4: ProfileInsert should have required fields
const testProfileInsert: ProfileInsert = {
  id: 'user123',
  username: 'newuser',
  email: 'new@example.com',
  hashed_password: 'hashed123',
  is_active: true,
  is_verified: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z'
  // full_name, preferences, last_login are optional
}

// If this file compiles without errors, the types are working correctly!
export { testTransaction, testTransactionInsert, testProfile, testProfileInsert }
