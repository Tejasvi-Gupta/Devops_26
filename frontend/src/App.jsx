import { AuthProvider, useAuth } from "./auth/AuthContext";
import Shell from "./components/Shell";
import InstructorPage from "./pages/InstructorPage";
import StudentPage from "./pages/StudentPage";
import LoginPage from "./pages/LoginPage";

function AppContent() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-[var(--color-muted)]">
        Loading...
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  return (
    <Shell>
      {user.role === "instructor" ? <InstructorPage /> : <StudentPage />}
    </Shell>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
