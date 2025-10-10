import { supabase } from './supabase'
import type { User as SupabaseUser } from '@supabase/supabase-js'

export interface AuthResponse {
  user: SupabaseUser | null
  error: string | null
}

export interface SignUpData {
  email: string
  password: string
  username?: string
  full_name?: string
}

export interface SignInData {
  email: string
  password: string
}

// Sign up with email and password
export async function signUp({ email, password, username, full_name }: SignUpData): Promise<AuthResponse> {
  try {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          username,
          full_name,
        }
      }
    })

    if (error) {
      return { user: null, error: error.message }
    }

    // Insert profile data
    if (data.user) {
      const { error: profileError } = await supabase
        .from('profiles')
        .insert({
          id: data.user.id,
          username,
          email,
          full_name,
        })

      if (profileError) {
        console.error('Error creating profile:', profileError)
        // Don't fail registration if profile creation fails
      }
    }

    return {
      user: data.user,
      error: null
    }
  } catch {
    return { user: null, error: 'An unexpected error occurred' }
  }
}

// Sign in with email and password
export async function signIn({ email, password }: SignInData): Promise<AuthResponse> {
  try {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })

    if (error) {
      return { user: null, error: error.message }
    }

    return {
      user: data.user,
      error: null
    }
  } catch {
    return { user: null, error: 'An unexpected error occurred' }
  }
}

// Sign out
export async function signOut(): Promise<{ error: string | null }> {
  try {
    const { error } = await supabase.auth.signOut()
    return { error: error?.message || null }
  } catch {
    return { error: 'An unexpected error occurred' }
  }
}

// Get current user
export async function getCurrentUser(): Promise<SupabaseUser | null> {
  try {
    const { data: { user } } = await supabase.auth.getUser()
    return user
  } catch {
    return null
  }
}

// Listen to auth state changes
export function onAuthStateChange(callback: (user: SupabaseUser | null) => void) {
  return supabase.auth.onAuthStateChange(async (event, session) => {
    callback(session?.user || null)
  })
}
