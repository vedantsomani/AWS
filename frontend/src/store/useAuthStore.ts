"use client";

import { create } from "zustand";
import {
  User,
  onAuthStateChanged,
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  GoogleAuthProvider,
  signOut as firebaseSignOut,
} from "firebase/auth";
import { doc, setDoc, serverTimestamp } from "firebase/firestore";
import { auth, db } from "@/lib/firebase/config";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
}

interface AuthActions {
  signInWithGoogle: () => Promise<void>;
  signInWithEmail: (email: string, password: string) => Promise<void>;
  signUpWithEmail: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  clearError: () => void;
  initialize: () => () => void;
}

type AuthStore = AuthState & AuthActions;

// ---------------------------------------------------------------------------
// Helper: Save user info to Firestore
// ---------------------------------------------------------------------------

async function saveUserToFirestore(user: User): Promise<void> {
  try {
    const userRef = doc(db, "users", user.uid);
    await setDoc(
      userRef,
      {
        email: user.email,
        displayName: user.displayName || null,
        photoURL: user.photoURL || null,
        lastLoginAt: serverTimestamp(),
        updatedAt: serverTimestamp(),
      },
      { merge: true }
    );
  } catch (error) {
    console.error("Failed to save user to Firestore:", error);
    // Don't throw - login should still succeed even if Firestore write fails
  }
}

async function createUserInFirestore(user: User): Promise<void> {
  try {
    const userRef = doc(db, "users", user.uid);
    await setDoc(userRef, {
      email: user.email,
      displayName: user.displayName || null,
      photoURL: user.photoURL || null,
      createdAt: serverTimestamp(),
      lastLoginAt: serverTimestamp(),
      updatedAt: serverTimestamp(),
    });
  } catch (error) {
    console.error("Failed to create user in Firestore:", error);
  }
}

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

const googleProvider = new GoogleAuthProvider();

export const useAuthStore = create<AuthStore>((set) => ({
  // State
  user: null,
  loading: true,
  error: null,

  // Actions
  signInWithGoogle: async () => {
    set({ loading: true, error: null });
    try {
      const result = await signInWithPopup(auth, googleProvider);
      await saveUserToFirestore(result.user);
      // User state will be updated by onAuthStateChanged listener
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to sign in with Google";
      set({ error: message, loading: false });
      throw error;
    }
  },

  signInWithEmail: async (email: string, password: string) => {
    set({ loading: true, error: null });
    try {
      const result = await signInWithEmailAndPassword(auth, email, password);
      await saveUserToFirestore(result.user);
      // User state will be updated by onAuthStateChanged listener
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to sign in";
      set({ error: message, loading: false });
      throw error;
    }
  },

  signUpWithEmail: async (email: string, password: string) => {
    set({ loading: true, error: null });
    try {
      const result = await createUserWithEmailAndPassword(auth, email, password);
      await createUserInFirestore(result.user);
      // User state will be updated by onAuthStateChanged listener
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to create account";
      set({ error: message, loading: false });
      throw error;
    }
  },

  signOut: async () => {
    set({ loading: true, error: null });
    try {
      await firebaseSignOut(auth);
      // User state will be updated by onAuthStateChanged listener
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to sign out";
      set({ error: message, loading: false });
      throw error;
    }
  },

  clearError: () => set({ error: null }),

  initialize: () => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      set({ user, loading: false });
    });
    return unsubscribe;
  },
}));
