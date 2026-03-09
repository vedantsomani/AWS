import { initializeApp, getApps, getApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyDEFLt_HbTqi3Rtmarss1h3A86_a4Xqqfw",
  authDomain: "multi-agent-ide.firebaseapp.com",
  projectId: "multi-agent-ide",
  storageBucket: "multi-agent-ide.firebasestorage.app",
  messagingSenderId: "56856538101",
  appId: "1:56856538101:web:b0481f4fdd5ee67ac80ebc",
  measurementId: "G-26G75SFPCE",
};

// Initialize Firebase (prevent multiple initializations)
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApp();
const auth = getAuth(app);
const db = getFirestore(app);

export { app, auth, db };
