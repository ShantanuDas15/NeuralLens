/**
 * Maps standard Firebase Auth error codes to user-friendly messages.
 */
export const getFirebaseErrorMessage = (error) => {
  const code = error?.code || error?.message || 'unknown';
  
  switch (code) {
    case 'auth/invalid-email':
      return 'The email address is invalid. Please check and try again.';
    case 'auth/user-disabled':
      return 'This account has been disabled. Please contact support.';
    case 'auth/user-not-found':
      return 'No account found with this email. Please sign up instead.';
    case 'auth/wrong-password':
    case 'auth/invalid-credential':
      return 'Incorrect email or password. Please try again.';
    case 'auth/email-already-in-use':
      return 'An account already exists with this email address. Please log in.';
    case 'auth/weak-password':
      return 'Your password is too weak. Please use at least 6 characters.';
    case 'auth/too-many-requests':
      return 'Too many failed attempts. Please try again later.';
    case 'auth/network-request-failed':
      return 'Network error. Please check your internet connection.';
    default:
      if (import.meta.env.DEV) console.error('Unhandled Auth Error:', error);
      return 'An unexpected authentication error occurred. Please try again.';
  }
};
