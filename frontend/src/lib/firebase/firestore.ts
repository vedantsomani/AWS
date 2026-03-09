import {
  collection,
  doc,
  addDoc,
  updateDoc,
  serverTimestamp,
  Timestamp,
} from "firebase/firestore";
import { db } from "@/lib/firebase/config";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ProjectRecord {
  id?: string;
  userId: string;
  prompt: string;
  status: "pending" | "running" | "completed" | "failed";
  createdAt: Timestamp;
  updatedAt: Timestamp;
  completedAt?: Timestamp;
  error?: string;
}

// ---------------------------------------------------------------------------
// Project Operations
// ---------------------------------------------------------------------------

/**
 * Create a new project record when user submits a prompt
 */
export async function createProjectRecord(
  userId: string,
  prompt: string
): Promise<string> {
  const projectsRef = collection(db, "users", userId, "projects");

  const docRef = await addDoc(projectsRef, {
    prompt,
    status: "running",
    createdAt: serverTimestamp(),
    updatedAt: serverTimestamp(),
  });

  return docRef.id;
}

/**
 * Update project status when generation completes
 */
export async function updateProjectStatus(
  userId: string,
  projectId: string,
  status: "completed" | "failed",
  error?: string
): Promise<void> {
  const projectRef = doc(db, "users", userId, "projects", projectId);

  const updateData: Record<string, unknown> = {
    status,
    updatedAt: serverTimestamp(),
  };

  if (status === "completed") {
    updateData.completedAt = serverTimestamp();
  }

  if (error) {
    updateData.error = error;
  }

  await updateDoc(projectRef, updateData);
}
